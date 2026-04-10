import { Component, JSX, splitProps } from "solid-js";

interface CardProps {
  title?: string;
  description?: string;
  children?: JSX.Element;
  footer?: JSX.Element;
  class?: string;
  style?: Record<string, string>;
  contentClass?: string;
}

export const Card: Component<CardProps> = (props) => {
  const [local, rest] = splitProps(props, ["title", "description", "children", "footer", "class", "style", "contentClass"]);

  return (
    <div
      class={`bg-background-light rounded-lg shadow-md overflow-hidden border border-gray-700 ${local.class || ''}`}
      style={local.style}
      {...rest}
    >
      <div class={`p-4 ${local.contentClass || ''}`}>
        {local.children}
      </div>
      {local.footer && (
        <div class="p-4 border-t border-gray-700">
          {local.footer}
        </div>
      )}
    </div>
  );
};
