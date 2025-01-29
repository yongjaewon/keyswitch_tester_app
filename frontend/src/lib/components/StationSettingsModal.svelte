<script lang="ts">
  import { appStore } from '../stores/appStore';
  import type { AppState, Station } from '../stores/appStore';

  export let station: Station;

  function closeModal() {
    appStore.update((state: AppState) => ({ 
      ...state, 
      showStationSettingsModal: false,
      selectedStation: null
    }));
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-xl">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Station {station.id} Settings</h2>
      <button on:click={closeModal} class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="flex flex-col gap-4">
      <!-- Station info -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Current Cycles</span>
          <span class="text-xl font-bold text-gray-900 dark:text-white">{station.currentCycles.toLocaleString()}</span>
        </div>

        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Motor Failures</span>
          <span class="text-xl font-bold text-gray-900 dark:text-white">{station.motorFailures}</span>
        </div>

        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Switch Failures</span>
          <span class="text-xl font-bold text-gray-900 dark:text-white">{station.switchFailures}</span>
        </div>

        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Status</span>
          <span class="text-xl font-bold text-gray-900 dark:text-white">{station.enabled ? 'Enabled' : 'Disabled'}</span>
        </div>
      </div>

      <div class="flex justify-end gap-4 mt-6">
        <button on:click={closeModal} 
                class="px-6 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
          Close
        </button>
      </div>
    </div>
  </div>
</div> 