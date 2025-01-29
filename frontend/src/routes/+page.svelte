<script lang="ts">
  import { onMount } from 'svelte';
  import { appStore, actions } from '$lib/stores/appStore';
  import type { AppState } from '$lib/stores/appStore';
  import { formatTime } from '$lib/utils';
  import StationCard from '$lib/components/StationCard.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';
  import TimerModal from '$lib/components/TimerModal.svelte';
  import StationSettingsModal from '$lib/components/StationSettingsModal.svelte';
  import { api, initializeWebSocket } from '$lib/services/api';

  let state: AppState;
  let indicatorVisible = true;
  let timer: ReturnType<typeof setInterval> | null = null;

  // Subscribe to store
  appStore.subscribe(newState => {
    state = newState;
  });

  // Add animation class for timer indicator
  onMount(() => {
    // Initialize WebSocket connection
    initializeWebSocket();

    const indicatorInterval = setInterval(() => {
      indicatorVisible = !indicatorVisible;
    }, 1000);

    // Load initial settings from the backend
    try {
      api.getSettings().then(settings => {
        actions.saveSettings(settings);
      });
    } catch (error) {
      console.error('Error loading settings:', error);
    }

    return () => {
      clearInterval(indicatorInterval);
      if (timer) clearInterval(timer);
    };
  });

  // Watch for timer state changes
  $: if (state.timerActive && !timer) {
    timer = setInterval(async () => {
      await actions.updateTimer();
    }, 1000);
  } else if (!state.timerActive && timer) {
    clearInterval(timer);
    timer = null;
  }

  // Watch for changes in failures and cycles and automatically disable station at thresholds
  $: {
    state.stations.forEach(station => {
      if ((station.switchFailures >= state.switchFailureThreshold || 
           station.motorFailures >= state.motorFailureThreshold ||
           station.currentCycles >= state.cycleLimit) && 
          station.enabled) {
        actions.toggleStation(station.id);
      }
    });
  }

  // Motor indicator states
  $: motorIndicatorStates = [
    { class: "bg-green-500 opacity-100" },             // Solid green
    { class: "bg-red-500 fast-blink" },               // Fast blinking red
    { class: "bg-green-500 slow-blink" },             // Slow blinking green
    { class: "bg-red-500 opacity-100" }               // Solid red
  ];

  // Switch indicator states
  $: switchIndicatorStates = [
    { class: "bg-red-500 opacity-100" },              // Solid red
    { class: "bg-green-500 slow-blink" },             // Slow blinking green
    { class: "bg-green-500 opacity-100" },            // Solid green
    { class: "bg-red-500 fast-blink" }                // Fast blinking red
  ];
</script>

<main class="w-[1024px] h-[600px] bg-gray-200 dark:bg-gray-900 p-6">
  <!-- Content area -->
  <div class="h-full flex flex-col">
    {#if state.currentPage === 'test'}
      <!-- Main content area -->
      <div class="h-full flex gap-6">
        <!-- Left side - Station cards -->
        <div class="flex-1 flex flex-col gap-4">
          {#each state.stations as station, index}
            <StationCard
              {station}
              motorIndicatorState={motorIndicatorStates[index].class}
              switchIndicatorState={switchIndicatorStates[index].class}
              motorCurrentThreshold={state.motorCurrentThreshold}
              switchCurrentThreshold={state.switchCurrentThreshold}
              motorFailureThreshold={state.motorFailureThreshold}
              switchFailureThreshold={state.switchFailureThreshold}
            />
          {/each}
        </div>

        <!-- Right side - Controls -->
        <div class="w-[340px] flex flex-col gap-6">
          <!-- Start/Stop button -->
          <button type="button" 
                  on:click={actions.toggleRunning}
                  class="text-white font-bold rounded-lg text-4xl px-5 h-36 transition-all border border-gray-300/90 shadow-md
                         {state.masterEnabled ? 'bg-red-600 active:bg-red-700 dark:bg-red-700 dark:active:bg-red-800' : 
                                        'bg-green-600 active:bg-green-700 dark:bg-green-700 dark:active:bg-green-800'}">
            {state.masterEnabled ? 'STOP' : 'START'}
          </button>

          <!-- Timer button -->
          <button type="button" 
                  on:click={() => {
                    if (state.timerActive) {
                      appStore.update(s => ({
                        ...s,
                        timerActive: false,
                        timerHours: 0,
                        timerMinutes: 0,
                        timerSeconds: 0
                      }));
                    } else {
                      appStore.update(s => ({ ...s, showTimerModal: true }));
                    }
                  }}
                  class="relative text-white bg-gray-600 active:bg-gray-700 font-bold rounded-lg text-2xl px-5 h-16 dark:bg-gray-700 dark:active:bg-gray-800 transition-all flex items-center justify-center gap-2 border border-gray-300/90 shadow-md {state.timerActive ? 'border-4' : ''}"
                  class:border-red-500={state.timerActive && indicatorVisible}
                  class:border-transparent={state.timerActive && !indicatorVisible}>
            {#if state.timerHours === 0 && state.timerMinutes === 0}
              Set Timer
            {:else}
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {formatTime(state.timerHours, state.timerMinutes, state.timerSeconds)}
              {#if state.timerActive}
                <div class="absolute top-2 right-2 w-3 h-3 rounded-full bg-red-500" class:opacity-0={!indicatorVisible}></div>
              {/if}
            {/if}
          </button>

          <!-- Status area -->
          <button on:click={() => appStore.update(s => ({ ...s, showSettingsModal: true }))}
                  class="p-4 bg-white border border-gray-300/90 rounded-lg shadow-md dark:bg-gray-800 dark:border-gray-700 h-fit text-left">
            <div class="flex flex-col gap-4">
              <!-- Status items -->
              <div class="grid grid-cols-[auto,1fr] gap-x-8 gap-y-2 text-xl font-bold">
                <!-- Supply voltage -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Supply</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">{state.supplyVoltage.toFixed(1)} V</span>

                <!-- Cutoff voltage -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13v-2a1 1 0 00-1-1H4a1 1 0 00-1 1v2a1 1 0 001 1h16a1 1 0 001-1zM12 6v4m0 4v4"/>
                  </svg>
                  <span>Cutoff</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">{state.cutoffVoltage.toFixed(1)} V</span>

                <!-- Cycles per minute -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Speed</span>
                </div>
                <div class="text-gray-900 dark:text-white text-right whitespace-nowrap">{state.cyclesPerMinute} cyc/min</div>

                <!-- Motor Current Threshold -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="9" stroke-width="2" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                  </svg>
                  <span>Motor Current</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">> {state.motorCurrentThreshold} A</span>

                <!-- Switch Current Threshold -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="9" stroke-width="2" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                  </svg>
                  <span>Switch Current</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">> {state.switchCurrentThreshold} A</span>

                <!-- Motor failure threshold -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16V8L12 14L16 8V16" />
                  </svg>
                  <span>Motor Limit</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">{state.motorFailureThreshold} Fails</span>

                <!-- Switch failure threshold -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <rect x="4" y="4" width="16" height="16" rx="2" stroke-width="2" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10C15 8 13 8 12 8C11 8 9 8 9 10C9 12 15 12 15 14C15 16 13 16 12 16C11 16 9 16 9 14" />
                  </svg>
                  <span>Switch Limit</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">{state.switchFailureThreshold} Fails</span>

                <!-- Cycle limit -->
                <div class="flex gap-2 text-gray-600 dark:text-gray-400">
                  <svg class="w-6 h-6 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span>Cycle Limit</span>
                </div>
                <span class="text-gray-900 dark:text-white text-right">{state.cycleLimit.toLocaleString()}</span>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Modals -->
      {#if state.showSettingsModal}
        <SettingsModal />
      {/if}

      {#if state.showTimerModal}
        <TimerModal />
      {/if}

      {#if state.showStationSettingsModal && state.selectedStation}
        <StationSettingsModal station={state.selectedStation} />
      {/if}
    {:else}
      <!-- Data page content -->
      <div class="h-full bg-white dark:bg-gray-800 rounded-lg border border-gray-300/90 dark:border-gray-700 p-4">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Test Data</h1>
        <p class="text-gray-600 dark:text-gray-400">Data visualization coming soon...</p>
      </div>
    {/if}
  </div>
</main>

<style>
  main {
    width: 1024px;
    height: 600px;
    overflow: hidden;
  }

  /* Remove focus outlines globally */
  :global(*:focus) {
    outline: none;
  }

  @keyframes fastBlink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  @keyframes slowBlink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .fast-blink {
    animation: fastBlink 0.5s ease-in-out infinite;
  }

  .slow-blink {
    animation: slowBlink 2s ease-in-out infinite;
  }
</style>
