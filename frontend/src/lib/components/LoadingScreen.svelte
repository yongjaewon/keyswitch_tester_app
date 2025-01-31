<script lang="ts">
    import { connectionStore } from '../stores/connectionStore';
    import type { ConnectionState } from '../stores/connectionStore';
    import { fade } from 'svelte/transition';

    $: state = $connectionStore;
    $: showLoading = state.isInitializing;
    $: message = getLoadingMessage(state);

    function getLoadingMessage(state: ConnectionState): string {
        if (!state.isConnected) {
            if (state.hasReachedMaxAttempts) {
                return 'Connection failed';
            }
            return 'Connecting to server...';
        }
        if (!state.isDataLoaded) {
            return 'Synchronizing system state...';
        }
        return 'Starting application...';
    }

    function handleRetry() {
        connectionStore.retry();
    }
</script>

{#if showLoading}
    <div 
        class="fixed inset-0 bg-gray-900 bg-opacity-90 flex items-center justify-center z-50"
        transition:fade
    >
        <div class="text-center p-8 rounded-lg bg-gray-800 shadow-xl">
            {#if !state.hasReachedMaxAttempts}
                <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-6"></div>
            {/if}
            <h2 class="text-xl font-semibold text-white">{message}</h2>
            {#if state.hasReachedMaxAttempts}
                <button
                    on:click={handleRetry}
                    class="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                >
                    Try Again
                </button>
            {/if}
        </div>
    </div>
{/if} 