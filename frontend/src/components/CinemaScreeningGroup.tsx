import { Component, For, createSignal, onMount, onCleanup } from "solid-js";
import { CinemaScreening } from "../types/movie";

interface CinemaScreeningGroupProps {
  group: CinemaScreening;
}

const CinemaScreeningGroup: Component<CinemaScreeningGroupProps> = (props) => {
  // On phone and tablet (0-768px), always use column layout
  // On larger screens, use the dynamic layout based on available space
  const [useSingleLine, setUseSingleLine] = createSignal(true);
  const [containerRef, setContainerRef] = createSignal<HTMLDivElement>();

  const checkLayout = () => {
    if (window.innerWidth < 769) {
      // On phone and tablet, always use column layout
      setUseSingleLine(false);
    } else {
      // On larger screens, check if content fits in single line
      const container = containerRef();
      if (container) {
        // Create a test element to check if content fits in single line
        const testElement = document.createElement('div');
        testElement.className = 'flex flex-wrap gap-2 items-center whitespace-nowrap';

        props.group.languages.forEach((lang, index) => {
          const langSpan = document.createElement('span');
          langSpan.className = 'text-gray-600 text-sm';
          langSpan.textContent = `${lang.language}: ${lang.times.join(', ')}`;
          testElement.appendChild(langSpan);

          if (index < props.group.languages.length - 1) {
            const separator = document.createElement('span');
            separator.className = 'text-gray-400 text-sm mx-1';
            separator.textContent = '|';
            testElement.appendChild(separator);
          }
        });

        container.appendChild(testElement);

        // Check if test element wraps to multiple lines
        const testElementHeight = testElement.offsetHeight;
        const singleLineHeight = parseInt(getComputedStyle(testElement).lineHeight) || 20;

        setUseSingleLine(testElementHeight <= singleLineHeight * 1.5);
        container.removeChild(testElement);
      }
    }
  };

  onMount(() => {
    checkLayout();

    // Add resize event listener for responsive behavior
    const handleResize = () => {
      checkLayout();
    };

    window.addEventListener('resize', handleResize);

    onCleanup(() => {
      window.removeEventListener('resize', handleResize);
    });
  });

  return (
    <div class="bg-white bg-opacity-90 rounded-lg p-3">
      <div class="flex items-center mb-2">
        <span class="font-medium text-gray-800 uppercase text-sm">{props.group.cinema}</span>
      </div>

      <div ref={setContainerRef} class="ml-4">
        {useSingleLine() ? (
          <div class="flex flex-wrap gap-2 items-center">
            <For each={props.group.languages}>
              {(languageGroup, index) => (
                <>
                  <span class="text-gray-600 text-sm whitespace-nowrap mr-1">
                    {languageGroup.language}:
                  </span>
                  <For each={languageGroup.times}>
                    {(time) => (
                      <span class="px-2 py-1 bg-white rounded border text-xs text-gray-600 shadow-sm">{time}</span>
                    )}
                  </For>
                  {index() < props.group.languages.length - 1 &&
                    <span class="text-gray-400 text-sm mx-1">|</span>}
                </>
              )}
            </For>
          </div>
        ) : (
          <div class="space-y-2">
            <For each={props.group.languages}>
              {(languageGroup) => (
                <div class="flex items-start gap-2">
                  <span class="text-gray-600 text-sm whitespace-nowrap pt-1">{languageGroup.language}:</span>
                  <div class="flex flex-wrap gap-1">
                    <For each={languageGroup.times}>
                      {(time) => (
                        <span class="px-2 py-1 bg-white rounded border text-xs text-gray-600 shadow-sm">{time}</span>
                      )}
                    </For>
                  </div>
                </div>
              )}
            </For>
          </div>
        )}
      </div>
    </div>
  );
};

export default CinemaScreeningGroup;
