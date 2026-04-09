import { For } from "solid-js";
import { formatDate, isSameDay } from "../utils/date";

interface DaySliderProps {
  dates: Date[];
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
}

export default function DaysSlider(props: DaySliderProps) {
  return (
    <div class="mb-8">
      <div class="flex overflow-x-auto space-x-2 pb-2">
        <For each={props.dates}>
          {(date) => (
         <button
            class={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
              isSameDay(date, props.selectedDate)
                ? 'bg-sky-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            onClick={() => props.onDateSelect(date)}
          >
            {formatDate(date)}
          </button>
          )}
        </For>
      </div>
    </div>
  );
}
