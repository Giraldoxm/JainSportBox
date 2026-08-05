using System;
using System.Drawing;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace HuelleroBridge
{

    // Ventana invisible — solo existe para proveer el HWND y message pump COM que
    // necesita el SDK de DigitalPersona para despachar eventos. Se posiciona fuera de
    // pantalla con tamaño 1×1 y opacidad 0 para que nunca sea visible. La captura en
    // background no depende de esta ventana sino de Priority.High en FingerprintCapture.
    internal class BridgeForm : Form
    {
        private readonly FingerprintCapture _capture;
        private readonly EnrollmentState    _state;
        private readonly RelayController    _relay;
        private System.Windows.Forms.Timer  _reloadTimer;

        public FingerprintCapture Capture => _capture;
        public RelayController    Relay   => _relay;

        // No activar la ventana al mostrarse (el HWND existe pero nunca toma foco)
        protected override bool ShowWithoutActivation => true;

        public BridgeForm(EnrollmentState state, WebSocketHub hub)
        {
            ShowInTaskbar   = false;
            FormBorderStyle = FormBorderStyle.None;
            WindowState     = FormWindowState.Normal;
            StartPosition   = FormStartPosition.Manual;
            Location        = new Point(-32000, -32000);
            Width           = 1;
            Height          = 1;
            Opacity         = 0;

            _state   = state;
            _relay   = new RelayController();
            _capture = new FingerprintCapture(state, json => hub.Broadcast(json), _relay);
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            // Conectar a la palanquera (Arduino). No bloquea ni falla si no está presente.
            _relay.Iniciar();
            // Iniciar captura una vez que la ventana (y su HWND) existen
            _capture.Start();
            Console.WriteLine("Presiona Ctrl+C para salir.");

            // Arranque automático del modo acceso: el gimnasio queda activo todo el horario.
            // Se carga el cache de templates y se entra en estado AccesoActivo. Cada huella
            // que se coloque (cuando no hay enrolamiento ni verify activos) registra
            // entrada/salida automáticamente en el backend.
            _ = IniciarAccesoAuto();

            // Refresco periódico de templates (5 min) para captar enrolamientos hechos
            // desde otra terminal o el frontend.
            _reloadTimer = new System.Windows.Forms.Timer { Interval = 5 * 60 * 1000 };
            _reloadTimer.Tick += async (s, ev) => await _capture.RecargarTemplatesAsync();
            _reloadTimer.Start();
        }

        private async Task IniciarAccesoAuto()
        {
            // La carga inicial puede fallar por transporte si el bridge arranca antes de
            // que la red esté lista — el caso típico al encender la PC del gym con el
            // bridge en Task Scheduler. Sin reintento quedarían hasta 5 minutos (el
            // intervalo de _reloadTimer) con el cache vacío, y con el cache vacío ninguna
            // huella coincide: el lector "no reconoce a nadie" sin ningún error visible.
            // RecargarTemplatesAsync no lanza: devuelve -1 si falló.
            int[] esperas = { 3, 10, 30 };
            int n = -1;
            for (int intento = 0; ; intento++)
            {
                n = await _capture.RecargarTemplatesAsync();
                if (n >= 0 || intento >= esperas.Length) break;
                Console.WriteLine($"[ACCESO] Falló la carga de templates. Reintento en {esperas[intento]}s…");
                await Task.Delay(esperas[intento] * 1000);
            }

            _state.IniciarAcceso();

            // Los tres desenlaces se loguean distinto a propósito: "0 cargados" y "falló
            // la carga" se ven igual desde el mostrador (el lector no reconoce a nadie)
            // pero se arreglan de forma completamente distinta.
            if (n < 0)
                Console.WriteLine($"[ACCESO] ACTIVO pero SIN templates: no se pudo consultar {BridgeConfig.ApiBase}. " +
                                  "El timer reintenta cada 5 min. Ninguna huella se reconocerá hasta que cargue.");
            else if (n == 0)
                Console.WriteLine("[ACCESO] ACTIVO pero el backend no tiene NINGUNA huella enrolada. " +
                                  "Enrolar desde el perfil del cliente (card \"Huella digital\").");
            else
                Console.WriteLine($"[ACCESO] Modo acceso permanente ACTIVO ({n} huellas cargadas).");
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _reloadTimer?.Stop();
            _capture.Stop();
            _relay.Detener();
            base.OnFormClosed(e);
        }
    }
}
