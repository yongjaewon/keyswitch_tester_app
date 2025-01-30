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
  timerHours: number;
  timerMinutes: number;
  timerSeconds: number;
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
  timerHours: 0,
  timerMinutes: 0,
  timerSeconds: 0,
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
        // Only update if we're not in a modal
        if (state.showTimerModal || state.showSettingsModal || state.showStationSettingsModal) {
            return state;
        }

        // Update stations with new data
        const updatedStations = state.stations.map(station => {
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

        return {
            ...state,
            supplyVoltage: data.supplyVoltage,
            masterEnabled: data.masterEnabled,
            stations: updatedStations
        };
    });
});

onMessage('timerUpdate', (data) => {
  appStore.update(state => {
    // Only update if we're not in timer modal
    if (state.showTimerModal) {
      return state;
    }
    return {
      ...state,
      timerHours: data.hours,
      timerMinutes: data.minutes,
      timerSeconds: data.seconds
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
          newState.timerHours = 0;
          newState.timerMinutes = 0;
          newState.timerSeconds = 0;
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

  updateTimer: async () => {
    const state = get(appStore);
    if (!state.timerActive) return;

    let { timerHours, timerMinutes, timerSeconds } = state;
    
    if (timerSeconds > 0) {
      timerSeconds--;
    } else if (timerMinutes > 0) {
      timerMinutes--;
      timerSeconds = 59;
    } else if (timerHours > 0) {
      timerHours--;
      timerMinutes = 59;
      timerSeconds = 59;
    } else {
      appStore.update(state => ({ ...state, timerActive: false }));
      return;
    }

    // Update both frontend and backend
    try {
      await api.setTimer(timerHours, timerMinutes);
      appStore.update(state => ({ 
        ...state, 
        timerHours, 
        timerMinutes, 
        timerSeconds 
      }));
    } catch (error) {
      console.error('Error updating timer:', error);
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
    const previousState = get(appStore);
    
    try {
      // Call APIs first
      await api.setTimer(hours, minutes);
      if (hours > 0 || minutes > 0) {
        await api.startTest();
      }

      // Update state only after successful API calls
      appStore.update(state => ({
        ...state,
        timerHours: hours,
        timerMinutes: minutes,
        timerSeconds: 0,
        timerActive: hours > 0 || minutes > 0,
        showTimerModal: false,
        masterEnabled: (hours > 0 || minutes > 0) ? true : state.masterEnabled
      }));
    } catch (error) {
      console.error('Error setting timer:', error);
      // Revert the state if the API call fails
      appStore.update(() => previousState);
    }
  }
}; 