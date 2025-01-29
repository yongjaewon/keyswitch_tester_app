export function formatTime(hours: number, minutes: number, seconds: number): string {
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

export function getCurrentBadgeClass(current: string, threshold: number): string {
  const value = parseFloat(current);
  if (value > threshold) {
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
  }
  return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
}

export function getFailureBadgeClass(failures: number, threshold: number): string {
  if (failures >= threshold) {
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
  }
  return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
} 