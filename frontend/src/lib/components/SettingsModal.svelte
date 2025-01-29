<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState } from '../stores/appStore';

  let editingSettings: Partial<AppState> = {};

  // Subscribe to store to initialize editing values
  appStore.subscribe((state: AppState) => {
    editingSettings = {
      cutoffVoltage: state.cutoffVoltage,
      motorCurrentThreshold: state.motorCurrentThreshold,
      switchCurrentThreshold: state.switchCurrentThreshold,
      cycleLimit: state.cycleLimit,
      motorFailureThreshold: state.motorFailureThreshold,
      switchFailureThreshold: state.switchFailureThreshold,
      cyclesPerMinute: state.cyclesPerMinute
    };
  });

  function closeModal() {
    appStore.update((state: AppState) => ({ ...state, showSettingsModal: false }));
  }

  async function saveSettings() {
    await actions.saveSettings(editingSettings);
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-[600px] shadow-xl">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">System Settings</h2>
      <button on:click={closeModal} class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="flex flex-col gap-4">
      <!-- Settings form -->
      <div class="grid grid-cols-2 gap-4">
        <!-- Cutoff Voltage -->
        <div class="flex flex-col gap-1">
          <label for="cutoffVoltage" class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Cutoff Voltage (V)
          </label>
          <input
            id="cutoffVoltage"
            type="number"
            bind:value={editingSettings.cutoffVoltage}
            min="0"
            step="0.1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Motor Current Threshold -->
        <div class="flex flex-col gap-1">
          <label for="motorCurrentThreshold" class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Motor Current Threshold (A)
          </label>
          <input
            id="motorCurrentThreshold"
            type="number"
            bind:value={editingSettings.motorCurrentThreshold}
            min="0"
            step="0.1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Switch Current Threshold -->
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Switch Current Threshold (A)
          </label>
          <input
            type="number"
            bind:value={editingSettings.switchCurrentThreshold}
            min="0"
            step="0.1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Cycle Limit -->
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Cycle Limit
          </label>
          <input
            type="number"
            bind:value={editingSettings.cycleLimit}
            min="0"
            step="1000"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Motor Failure Threshold -->
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Motor Failure Threshold
          </label>
          <input
            type="number"
            bind:value={editingSettings.motorFailureThreshold}
            min="0"
            step="1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Switch Failure Threshold -->
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Switch Failure Threshold
          </label>
          <input
            type="number"
            bind:value={editingSettings.switchFailureThreshold}
            min="0"
            step="1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>

        <!-- Cycles Per Minute -->
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Cycles Per Minute
          </label>
          <input
            type="number"
            bind:value={editingSettings.cyclesPerMinute}
            min="1"
            max="60"
            step="1"
            class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
          />
        </div>
      </div>

      <div class="flex justify-end gap-4 mt-6">
        <button on:click={closeModal} 
                class="px-6 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
          Cancel
        </button>
        <button on:click={saveSettings}
                class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800">
          Save Settings
        </button>
      </div>
    </div>
  </div>
</div> 