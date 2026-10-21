"use client";

import { useEffect, useRef } from "react";
import { Compartment, EditorState } from "@codemirror/state";
import { defaultHighlightStyle, syntaxHighlighting, StreamLanguage } from "@codemirror/language";
import { verilog } from "@codemirror/legacy-modes/mode/verilog";
import { python } from "@codemirror/legacy-modes/mode/python";
import { drawSelection, EditorView, highlightActiveLine, keymap, lineNumbers } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";

type Props = { value: string; onChange: (value: string) => void; onCompile: () => void; disabled?: boolean; focusLine?: number | null; language?: "python" | "verilog" };

export function VerilogEditor({ value, onChange, onCompile, disabled = false, focusLine, language = "verilog" }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);
  const onCompileRef = useRef(onCompile);
  const editableRef = useRef(new Compartment());
  const initialValueRef = useRef(value);
  const initialDisabledRef = useRef(disabled);
  const initialLanguageRef = useRef(language);
  onChangeRef.current = onChange;
  onCompileRef.current = onCompile;

  useEffect(() => {
    if (!host.current) return;
    const state = EditorState.create({
      doc: initialValueRef.current,
      extensions: [
        lineNumbers(),
        history(),
        drawSelection(),
        highlightActiveLine(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        StreamLanguage.define(initialLanguageRef.current === "python" ? python : verilog),
        editableRef.current.of(EditorView.editable.of(!initialDisabledRef.current)),
        keymap.of([
          ...defaultKeymap,
          ...historyKeymap,
          indentWithTab,
          { key: "Mod-Enter", run: () => { onCompileRef.current(); return true; } },
        ]),
        EditorView.theme({ "&": { minHeight: "340px" }, ".cm-scroller": { overflow: "auto", fontFamily: "var(--font-geist-mono)" }, ".cm-content": { padding: "18px 0" }, ".cm-gutters": { padding: "18px 0" } }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) onChangeRef.current(update.state.doc.toString());
        }),
      ],
    });
    const view = new EditorView({ state, parent: host.current });
    view.dom.setAttribute("aria-label", `${initialLanguageRef.current} source editor`);
    viewRef.current = view;
    return () => { view.destroy(); viewRef.current = null; };
  }, []);

  useEffect(() => {
    const view = viewRef.current;
    if (!view || !focusLine) return;
    const line = view.state.doc.line(Math.min(focusLine, view.state.doc.lines));
    view.dispatch({ selection: { anchor: line.from }, effects: EditorView.scrollIntoView(line.from, { y: "center" }) });
    view.focus();
  }, [focusLine]);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    view.dom.setAttribute("aria-disabled", String(disabled));
    view.dispatch({ effects: editableRef.current.reconfigure(EditorView.editable.of(!disabled)) });
  }, [disabled]);

  return <div className="editor-shell" ref={host} />;
}
