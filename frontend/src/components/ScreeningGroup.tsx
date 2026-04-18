import { Component, For } from "solid-js";
import { OrganizedScreening } from "~/types/movie";

interface ScreeningGroupProps {
  group: OrganizedScreening;
}

const ScreeningGroup: Component<ScreeningGroupProps> = (props) => {
  return (
     <div class="screening-group rounded-lg p-3">
      <div class="flex items-center mb-2">
         <span class="font-medium uppercase text-sm">{props.group.language}</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <For each={props.group.times}>
          {(time) => {
            // Use the URL from the API (stored during scraping)
            const screeningUrl = props.group.url || "#";
            return (
                  <a
                   href={screeningUrl}
                   target="_blank"
                   rel="noopener noreferrer"
                   class="px-3 py-1 bg-gray-800 rounded border text-sm shadow-sm hover:bg-gray-700 transition-colors cursor-pointer screening-time"
                 >
                {time}
              </a>
            );
          }}
        </For>
      </div>
    </div>
  );
};

export default ScreeningGroup;
