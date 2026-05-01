using System;
using System.Windows.Forms;

namespace HuelleroBridge
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            Console.Title = "JainSportBox - Huellero Bridge";
            Console.WriteLine("=== Huellero Bridge (DigitalPersona U.are.U 4500) ===");

            var state = new EnrollmentState();

            var hub = new WebSocketHub("ws://0.0.0.0:8765");
            hub.Start();
            Console.WriteLine("[WS] Escuchando en ws://localhost:8765");

            var form = new BridgeForm(state, hub);

            // HttpApi necesita referencia al capture para cargar templates en verify mode
            // BridgeForm crea el capture; lo pasamos después de construir el form
            var api = new HttpApi(state, form.Capture, port: 8001);
            api.Start();

            Console.CancelKeyPress += (_, e) => { e.Cancel = true; Application.Exit(); };
            Application.Run(form);
            Console.WriteLine("Bye.");
        }
    }
}
