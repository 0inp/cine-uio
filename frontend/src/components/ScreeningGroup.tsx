import { Component, For } from "solid-js";
import { OrganizedScreening } from "../types/movie";

interface ScreeningGroupProps {
  group: OrganizedScreening;
}

const ScreeningGroup: Component<ScreeningGroupProps> = (props) => {
  return (
    <div class="bg-white bg-opacity-90 rounded-lg p-3">
      <div class="flex items-center mb-2">
        <span class="font-medium text-gray-800 uppercase text-sm">{props.group.language}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <For each={props.group.times}>
          {(time) => (
            <span class="px-3 py-1 bg-white rounded border text-sm text-gray-600 shadow-sm">{time}</span>
          )}
        </For>
      </div>
    </div>
  );
};

export default ScreeningGroup;
