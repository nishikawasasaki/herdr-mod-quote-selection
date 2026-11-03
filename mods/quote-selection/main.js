import { View, div } from "gpui-kit";
import { focused, props, exec, appHome, closeOverlay, run, notify } from "herdr";

export default class Annotation extends View {
  init(_props, cx) {
    this.error = "";
    const overlay = props()?.overlay;
    const terminal = focused()?.terminal;
    if (!terminal) {
      this.error = "引用先のターミナルを選択してください。";
      notify({ title: "Quote Selection", body: this.error, level: "error" });
      if (overlay) closeOverlay(overlay);
      return;
    }
    cx.spawn(async (cx) => {
      try {
        const selection = await exec("/usr/bin/env", ["LC_ALL=en_US.UTF-8", "/usr/bin/pbpaste"]);
        if (selection.code !== 0) throw new Error("選択した文章を読み取れませんでした。");
        const result = await exec("python3", [appHome() + "/mods/quote-selection/quote.py", "--", terminal, selection.stdout]);
        if (result.code !== 0) throw new Error(result.stdout.trim() || "引用を追加できませんでした。");
      } catch (error) {
        this.error = String(error.message ?? error);
        notify({ title: "Quote Selection", body: this.error, level: "error" });
      } finally {
        if (overlay) closeOverlay(overlay);
        run("pane.focus", { terminal });
      }
    });
  }

  render(cx) {
    return div().size(0);
  }
}
