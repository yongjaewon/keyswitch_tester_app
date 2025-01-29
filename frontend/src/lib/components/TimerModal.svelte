<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { AppState } from '../stores/appStore';
  import { TIMER_SETTINGS } from '../constants';

  let editingHours = 0;
  let editingMinutes = 0;

  // Subscribe to store to initialize editing values
  appStore.subscribe((state: AppState) => {
    editingHours = state.timerHours;
    editingMinutes = state.timerMinutes;
  });

  function closeModal() {
    appStore.update((state: AppState) => ({ ...state, showTimerModal: false }));
  }

  async function saveTimer() {
    await actions.setTimer(editingHours, editingMinutes);
  }

  function incrementHours() {
    editingHours = (editingHours + 1) % (TIMER_SETTINGS.MAX_HOURS + 1);
  }

  function decrementHours() {
    editingHours = editingHours > 0 ? editingHours - 1 : TIMER_SETTINGS.MAX_HOURS;
  }

  function incrementMinutes() {
    editingMinutes = (editingMinutes + TIMER_SETTINGS.MINUTE_STEP) % 60;
  }

  function decrementMinutes() {
    editingMinutes = editingMinutes >= TIMER_SETTINGS.MINUTE_STEP ? 
      editingMinutes - TIMER_SETTINGS.MINUTE_STEP : 
      60 - TIMER_SETTINGS.MINUTE_STEP;
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-xl">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Set Timer</h2>
      <button on:click={closeModal} class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="flex flex-col gap-4">
      <!-- Timer controls -->
      <div class="flex items-center justify-center gap-6 p-4">
        <!-- Hours -->
        <div class="flex flex-col items-center">
          <button on:click={incrementHours} 
                  class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <div class="w-24 h-20 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
            <span class="text-4xl font-bold text-gray-900 dark:text-white">
              {editingHours.toString().padStart(2, '0')}
            </span>
          </div>
          <button on:click={decrementHours}
                  class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <span class="text-xl text-gray-600 dark:text-gray-400 mt-2 font-medium">Hours</span>
        </div>

        <span class="text-4xl font-bold text-gray-900 dark:text-white mt-4">:</span>

        <!-- Minutes -->
        <div class="flex flex-col items-center">
          <button on:click={incrementMinutes}
                  class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <div class="w-24 h-20 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
            <span class="text-4xl font-bold text-gray-900 dark:text-white">
              {editingMinutes.toString().padStart(2, '0')}
            </span>
          </div>
          <button on:click={decrementMinutes}
                  class="p-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <span class="text-xl text-gray-600 dark:text-gray-400 mt-2 font-medium">Minutes</span>
        </div>
      </div>

      <div class="flex justify-end gap-4 mt-6">
        <button on:click={closeModal} 
                class="px-8 py-4 text-2xl text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
          Cancel
        </button>
        <button on:click={saveTimer}
                class="px-8 py-4 text-2xl bg-green-600 text-white rounded-lg hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800">
          Set Timer
        </button>
      </div>
    </div>
  </div>
</div> 
