using System;

namespace HuelleroBridge
{
    /// <summary>
    /// Configuración del bridge leída de variables de entorno, con defaults para
    /// desarrollo local. Fuente única de verdad para no desincronizar valores
    /// (sobre todo el secreto) entre FingerprintCapture y HttpApi.
    /// </summary>
    public static class BridgeConfig
    {
        /// <summary>
        /// Backend al que el bridge manda asistencias y templates de huella.
        /// Default: backend desplegado en Render (producción). Para apuntar a un
        /// backend local en desarrollo, definir JSB_API_BASE=http://localhost:8000.
        /// DEBE ser HTTPS en la nube para no exponer X-Bridge-Secret.
        /// Se lee UNA sola vez al arrancar: tras cambiar la env var hay que
        /// reiniciar el bridge y confirmar la línea [CONFIG] ApiBase del log.
        /// </summary>
        public static readonly string ApiBase =
            (Environment.GetEnvironmentVariable("JSB_API_BASE")
                ?? "https://jainsportbox-api.onrender.com").TrimEnd('/');

        /// <summary>
        /// Clave compartida con el backend (header X-Bridge-Secret). Debe
        /// coincidir con BRIDGE_SECRET del backend.
        /// </summary>
        public static readonly string BridgeSecret =
            Environment.GetEnvironmentVariable("BRIDGE_SECRET") ?? "jain_bridge_secret_2024";
    }
}
