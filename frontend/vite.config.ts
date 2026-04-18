import { defineConfig } from "vite";
import { nitroV2Plugin as nitro } from "@solidjs/vite-plugin-nitro-2";
import { solidStart } from "@solidjs/start/config";
import UnoCSS from "unocss/vite";
import presetWind4 from "@unocss/preset-wind4";
import path from "path";

export default defineConfig({
  plugins: [
    solidStart(),
    UnoCSS({
      presets: [presetWind4()]
    }),
    nitro()
  ],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "./src")
    }
  }
});
