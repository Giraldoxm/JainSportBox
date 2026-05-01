using System;
using System.Windows.Forms;

namespace HuelleroBridge
{
    // Ventana completamente oculta — solo existe para proveer el message pump y HWND
    // que necesita el SDK de DigitalPersona para despachar eventos COM.
    internal class BridgeForm : Form
    {
        private readonly FingerprintCapture _capture;

        public FingerprintCapture Capture => _capture;

        public BridgeForm(EnrollmentState state, WebSocketHub hub)
        {
            // Ocultar completamente de taskbar y pantalla
            ShowInTaskbar  = false;
            WindowState    = FormWindowState.Minimized;
            FormBorderStyle = FormBorderStyle.None;
            Opacity        = 0;
            Width  = 1;
            Height = 1;

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
