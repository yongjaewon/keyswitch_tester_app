<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { initializeWebSocket } from '$lib/services/api';
  import LoadingScreen from '$lib/components/LoadingScreen.svelte';
  import ReconnectionDialog from '$lib/components/ReconnectionDialog.svelte';
  import { connectionStore } from '$lib/stores/connectionStore';

  onMount(() => {
    initializeWebSocket();
    return () => {
      connectionStore.reset();
    };
  });
</script>

<LoadingScreen />
<ReconnectionDialog />

<main class="min-h-screen bg-gray-900 text-white">
  <slot />
</main> 