<script lang="ts">
  import { appStore, actions } from '../stores/appStore';
  import type { Station } from '../stores/appStore';
  import { getCurrentBadgeClass, getFailureBadgeClass } from '../utils';

  export let station: Station;
  export let motorIndicatorState: string;
  export let switchIndicatorState: string;
  export let motorCurrentThreshold: number;
  export let switchCurrentThreshold: number;
  export let motorFailureThreshold: number;
  export let switchFailureThreshold: number;

  function showSettings() {
    appStore.update(state => ({
      ...state,
      selectedStation: station,
      showStationSettingsModal: true
    }));
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-300/90 dark:border-gray-700 shadow-md">
  <div class="p-4">
    <div class="flex items-center">
      <!-- Station info -->
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">Station {station.id}</h3>
          <button on:click={showSettings} class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
        <div class="text-lg text-gray-600 dark:text-gray-400 mt-1">
          {station.currentCycles.toLocaleString()} cycles
        </div>
      </div>

      <!-- Failure indicators -->
      <div class="flex items-center">
        <div class="flex-1 flex flex-col items-center px-2">
          <div class="relative flex items-center h-6">
            <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Motor</span>
            <div class="absolute -right-3 w-2 h-2 rounded-full {motorIndicatorState}"></div>
          </div>
          <div class="flex flex-col items-center w-[120px]">
            <span class="text-xl font-bold px-3 py-0.5 rounded-full {getCurrentBadgeClass(station.motorCurrent, motorCurrentThreshold)}">
              {station.motorCurrent}
            </span>
            <span class="text-xl font-bold px-3 py-0.5 rounded-full mt-1 {getFailureBadgeClass(station.motorFailures, motorFailureThreshold)}">
              {station.motorFailures} Fails
            </span>
          </div>
        </div>

        <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>

        <div class="flex-1 flex flex-col items-center px-2">
          <div class="relative flex items-center h-6">
            <span class="text-base font-semibold text-gray-700 dark:text-gray-300">Switch</span>
            <div class="absolute -right-3 w-2 h-2 rounded-full {switchIndicatorState}"></div>
          </div>
          <div class="flex flex-col items-center w-[120px]">
            <span class="text-xl font-bold px-3 py-0.5 rounded-full {getCurrentBadgeClass(station.switchCurrent, switchCurrentThreshold)}">
              {station.switchCurrent}
            </span>
            <span class="text-xl font-bold px-3 py-0.5 rounded-full mt-1 {getFailureBadgeClass(station.switchFailures, switchFailureThreshold)}">
              {station.switchFailures} Fails
            </span>
          </div>
        </div>

        <div class="h-16 w-px bg-gray-400 dark:bg-gray-500"></div>
      </div>

      <!-- Toggle switch -->
      <div class="ml-4 mr-2">
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" 
                 checked={station.enabled}
                 on:change={() => actions.toggleStation(station.id)}
                 class="sr-only peer">
          <div class="w-[72px] h-10 bg-gray-300 border border-gray-300 rounded-full peer dark:bg-gray-600 dark:border-gray-600 peer-checked:after:translate-x-8 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:border-gray-300 after:rounded-full after:h-9 after:w-9 after:transition-all peer-checked:bg-green-600 peer-checked:border-green-600"></div>
        </label>
      </div>
    </div>
  </div>
</div>

<style>
  /* Component-specific styles can go here */
</style> 