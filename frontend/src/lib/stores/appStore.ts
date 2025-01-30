import { writable, get } from 'svelte/store';
import { api, initializeWebSocket, onMessage } from '../services/api';

// Types
export interface Station {
  id: number;
  enabled: boolean;
  motorFailures: number;
  switchFailures: number;
  currentCycles: number;
  motorCurrent: string;
  switchCurrent: string;
}

export interface AppState {
  currentPage: 'test' | 'data';
  showTimerModal: boolean;
  showSettingsModal: boolean;
  showStationSettingsModal: boolean;
  masterEnabled: boolean;
  cutoffVoltage: number;
  motorFailureThreshold: number;
  switchFailureThreshold: number;
  cycleLimit: number;
  motorCurrentThreshold: number;
  switchCurrentThreshold: number;
  cyclesPerMinute: number;
  timerEndTime: string | null;
  timerActive: boolean;
  stations: Station[];
  selectedStation: Station | null;
  supplyVoltage: number;
}

// Initial state
const initialState: AppState = {
  currentPage: 'test',
  showTimerModal: false,
  showSettingsModal: false,
  showStationSettingsModal: false,
  masterEnabled: false,
  cutoffVoltage: 11.1,
  motorFailureThreshold: 10,
  switchFailureThreshold: 10,
  cycleLimit: 100000,
  motorCurrentThreshold: 100,
  switchCurrentThreshold: 5,
  cyclesPerMinute: 6,
  timerEndTime: null,
  timerActive: false,
  selectedStation: null,
  supplyVoltage: 13.2,
  stations: [1, 2, 3, 4].map(id => ({
    id,
    enabled: false,
    motorFailures: 0,
    switchFailures: 0,
    currentCycles: 0,
    motorCurrent: "0.0 A",
    switchCurrent: "0.0 A"
  }))
};

// Create the store
export const appStore = writable<AppState>(initialState);

// Track pending state changes
let pendingStateChanges: { [key: string]: boolean } = {};

// Register WebSocket message handlers
onMessage('status_update', (data: {
    supplyVoltage: number;
    masterEnabled: boolean;
    timerActive: boolean;
    timerEndTime: string | null;
    stations: {
        id: number;
        enabled: boolean;
        motorFailures: number;
        switchFailures: number;
        currentCycles: number;
        motorCurrent: number;
        switchCurrent: number;
    }[];
}) => {
    appStore.update(state => {
        // Update stations with new data, but only if not in a modal
        const updatedStations = state.showTimerModal || state.showSettingsModal || state.showStationSettingsModal
            ? state.stations
            : state.stations.map(station => {
                const newData = data.stations.find(s => s.id === station.id);
                if (newData) {
                    // If we have a pending state change for this station, don't update its enabled state
                    const pendingKey = `station_${station.id}`;
                    if (pendingStateChanges[pendingKey]) {
                        return {
                            ...station,
                            motorFailures: newData.motorFailures,
                            switchFailures: newData.switchFailures,
                            currentCycles: newData.currentCycles,
                            motorCurrent: `${newData.motorCurrent.toFixed(1)} A`,
                            switchCurrent: `${newData.switchCurrent.toFixed(1)} A`
                        };
                    }
                    return {
                        ...station,
                        enabled: newData.enabled,
                        motorFailures: newData.motorFailures,
                        switchFailures: newData.switchFailures,
                        currentCycles: newData.currentCycles,
                        motorCurrent: `${newData.motorCurrent.toFixed(1)} A`,
                        switchCurrent: `${newData.switchCurrent.toFixed(1)} A`
                    };
                }
                return station;
            });

        // Always update timer and system state, regardless of modal state
        return {
            ...state,
            supplyVoltage: data.supplyVoltage,
            masterEnabled: data.masterEnabled,
            timerActive: data.timerActive,
            timerEndTime: data.timerEndTime,
            stations: updatedStations
        };
    });
});

// Store actions
export const actions = {
  toggleRunning: async () => {
    const state = get(appStore);
    const newMasterEnabled = !state.masterEnabled;

    try {
      // Call the API first
      if (newMasterEnabled) {
        await api.startTest();
      } else {
        await api.stopTest();
      }

      // Update state only after successful API call
      appStore.update(state => {
        const newState = { ...state, masterEnabled: newMasterEnabled };
        if (!newState.masterEnabled && newState.timerActive) {
          newState.timerActive = false;
          newState.timerEndTime = null;
        }
        return newState;
      });
    } catch (error) {
      console.error('Error toggling test state:', error);
    }
  },

  setStationState: async (stationId: number, enabled: boolean) => {
    const pendingKey = `station_${stationId}`;
    pendingStateChanges[pendingKey] = true;
    
    let previousState: Station | undefined;
    
    appStore.update(state => {
      previousState = state.stations.find(s => s.id === stationId);
      return {
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId 
            ? { ...station, enabled: enabled }
            : station
        )
      };
    });

    try {
      await api.setStationState(stationId, enabled);
      // Clear the pending state after a successful update
      delete pendingStateChanges[pendingKey];
    } catch (error) {
      console.error('Error setting station state:', error);
      delete pendingStateChanges[pendingKey];
      // Revert the state if the API call fails
      appStore.update(state => ({
        ...state,
        stations: state.stations.map(station => 
          station.id === stationId && previousState
            ? { ...station, enabled: previousState.enabled }
            : station
        )
      }));
    }
  },

  saveSettings: async (settings: Partial<AppState>) => {
    const previousState = get(appStore);
    
    appStore.update(state => ({ ...state, ...settings }));

    // Call the API
    try {
      // Extract only the system settings fields
      const systemSettings = {
        cutoffVoltage: settings.cutoffVoltage!,
        motorCurrentThreshold: settings.motorCurrentThreshold!,
        switchCurrentThreshold: settings.switchCurrentThreshold!,
        cycleLimit: settings.cycleLimit!,
        motorFailureThreshold: settings.motorFailureThreshold!,
        switchFailureThreshold: settings.switchFailureThreshold!,
        cyclesPerMinute: settings.cyclesPerMinute!
      };
      await api.updateSettings(systemSettings);
    } catch (error) {
      console.error('Error saving settings:', error);
      // Revert the state if the API call fails
      appStore.update(() => previousState);
    }
  },

  setTimer: async (hours: number, minutes: number) => {
    try {
      const success = await api.setTimer(hours, minutes);
      if (success) {
        appStore.update(state => ({
          ...state,
          showTimerModal: false,
          timerActive: hours > 0 || minutes > 0
          // Let the backend's timerEndTime come through WebSocket
        }));
      }
    } catch (error) {
      console.error('Error setting timer:', error);
    }
  },

  clearTimer: async () => {
    try {
      const success = await api.setTimer(0, 0);
      if (success) {
        appStore.update(state => ({
          ...state,
          timerActive: false,
          timerEndTime: null
        }));
      }
    } catch (error) {
      console.error('Error clearing timer:', error);
    }
  }
}; 