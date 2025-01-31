<script lang="ts">
    import { connectionStore } from '../stores/connectionStore';
    import { fade } from 'svelte/transition';

    $: state = $connectionStore;
    $: showDialog = !state.isInitializing && !state.isConnected;

    function handleManualReconnect() {
        connectionStore.retry();
    }
</script>

{#if showDialog}
    <div 
        class="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50"
        transition:fade
    >
        <div class="bg-gray-800 px-8 pt-4 pb-8 rounded-lg shadow-xl max-w-md">
            <div class="text-center">
                <div class="text-red-500 text-5xl mb-4">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h2 class="text-xl font-bold text-white mb-6">Connection Lost</h2>
                <p class="text-gray-300 mb-6">
                    {#if state.hasReachedMaxAttempts}
                        Lost connection to the server.
                    {:else if state.reconnectAttempt > 0}
                        Attempting to reconnect...
                    {:else}
                        Lost connection to the server. The application will automatically attempt to reconnect.
                    {/if}
                </p>
                <div class="flex justify-center items-center gap-4">
                    {#if state.reconnectAttempt > 0 && !state.hasReachedMaxAttempts}
                        <div class="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
                    {:else}
                        <button
                            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                            on:click={handleManualReconnect}
                        >
                            Reconnect Now
                        </button>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if} 