<template>
  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-900 text-white flex flex-col shadow-xl">
      <div class="p-6 border-b border-gray-800 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h1 class="text-xl font-extrabold tracking-wider">CrossFit Box</h1>
      </div>
      <nav class="flex-1 mt-6 px-4 space-y-2">
        <router-link to="/usuarios" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-indigo-600 hover:bg-indigo-700 font-semibold shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          Usuarios
        </router-link>
        <router-link to="/tienda" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-indigo-600 hover:bg-indigo-700 font-semibold shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          Tienda POS
        </router-link>
      </nav>
      <div class="p-6 border-t border-gray-800 text-xs text-gray-500 text-center">
        &copy; 2026 Admin System
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-x-hidden overflow-y-auto">
      <div class="p-8">
        <router-view></router-view>
        <div v-if="$route.path === '/'" class="flex flex-col items-center justify-center h-full mt-20">
          <img src="https://ui-avatars.com/api/?name=CrossFit+Box&background=random" alt="Logo" class="w-24 h-24 rounded-full mb-6 shadow-lg" />
          <h2 class="text-4xl font-black text-gray-800 mb-4 tracking-tight">Bienvenido al Panel</h2>
          <p class="text-lg text-gray-500 max-w-md text-center">Selecciona una opción del menú lateral para gestionar los usuarios o realizar ventas en la tienda.</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
</script>
