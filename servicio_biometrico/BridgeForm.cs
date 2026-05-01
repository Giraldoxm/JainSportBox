using System;
using System.Drawing;
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

        public FingerprintCapture Capture => _capture;

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

            _capture = new FingerprintCapture(state, json => hub.Broadcast(json));
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            // Iniciar captura una vez que la ventana (y su HWND) existen
            _capture.Start();
            Console.WriteLine("Presiona Ctrl+C para salir.");
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _capture.Stop();
            base.OnFormClosed(e);
        }
    }
}
