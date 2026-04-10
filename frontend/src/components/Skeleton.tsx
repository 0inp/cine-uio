import { Component, splitProps, JSX } from "solid-js";

interface SkeletonProps {
  class?: string;
  children?: JSX.Element;
}

export const Skeleton: Component<SkeletonProps> = (props) => {
  const [local] = splitProps(props, ["class", "children"]);

  return (
    <div class={`animate-pulse bg-gray-800 rounded ${local.class || ''}`}>
      {local.children || <div class="h-full w-full"></div>}
    </div>
  );
};
