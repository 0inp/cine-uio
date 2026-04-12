// Date utility functions

export function formatDate(date: Date): string {
  return date.toLocaleDateString('es-ES', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

export function formatDateShort(date: Date): string {
  return date.toLocaleDateString('es-ES', {
    weekday: 'short'
  });
}

export function formatDayNumber(date: Date): string {
  return date.getDate().toString().padStart(2, '0');
}

export function isSameDay(date1: Date, date2: Date): boolean {
  return date1.toDateString() === date2.toDateString();
}

export function getDateRange(startDate: Date, days: number): Date[] {
  return Array.from({ length: days }, (_, i) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);
    return date;
  });
}
