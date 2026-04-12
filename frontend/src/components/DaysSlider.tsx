import { For } from "solid-js";
import { formatDate, formatDateShort, formatDayNumber, isSameDay } from "../utils/date";

interface DaySliderProps {
  dates: Date[];
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
}

export default function DaysSlider(props: DaySliderProps) {
  return (
    <div class="mb-8 w-full">
      <div class="flex justify-center overflow-x-auto space-x-2 pb-2">
        <div class="flex space-x-2">
          <For each={props.dates}>
            {(date) => (
              <button
                class={`flex flex-col items-center justify-center w-16 h-16 rounded-lg transition-all whitespace-nowrap flex-shrink-0 ${isSameDay(date, props.selectedDate)
                    ? 'bg-primary text-white'
                    : 'bg-text-secondary text-[rgb(24,22,22)] hover:border-card-border'
                  }`}
                onClick={() => props.onDateSelect(date)}
              >
                <span class="text-xs font-medium uppercase">{formatDateShort(date)}</span>
                <span class="text-lg font-bold">{formatDayNumber(date)}</span>
              </button>
            )}
          </For>
        </div>
      </div>
    </div>
  );
}
