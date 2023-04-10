import { BBox } from "./util/bbox";
import { Size, Box, Extents } from "./types";
export type { CSSStyles, CSSStylesNative, CSSOurStyles } from "./css";
export type HTMLAttrs = {
    [name: string]: unknown;
};
export type HTMLItem = string | Node | NodeList | HTMLCollection | null | undefined;
export type HTMLChild = HTMLItem | HTMLItem[];
export declare function createElement<T extends keyof HTMLElementTagNameMap>(tag: T, attrs: HTMLAttrs | null, ...children: HTMLChild[]): HTMLElementTagNameMap[T];
export declare const div: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLDivElement, span: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLSpanElement, canvas: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLCanvasElement, link: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLLinkElement, style: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLStyleElement, a: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLAnchorElement, p: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLParagraphElement, i: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLElement, pre: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLPreElement, button: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLButtonElement, label: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLLabelElement, legend: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLLegendElement, fieldset: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLFieldSetElement, input: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLInputElement, select: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLSelectElement, option: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLOptionElement, optgroup: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLOptGroupElement, textarea: (attrs?: HTMLAttrs | HTMLChild, ...children: HTMLChild[]) => HTMLTextAreaElement;
export type SVGAttrs = {
    [key: string]: string | false | null | undefined;
};
export declare function createSVGElement<T extends keyof SVGElementTagNameMap>(tag: T, attrs?: SVGAttrs | null, ...children: HTMLChild[]): SVGElementTagNameMap[T];
export declare function text(str: string): Text;
export declare function nbsp(): Text;
export declare function append(element: Node, ...children: Node[]): void;
export declare function remove(element: Node): void;
export declare function replaceWith(element: Node, replacement: Node): void;
export declare function prepend(element: Node, ...nodes: Node[]): void;
export declare function empty(node: Node, attrs?: boolean): void;
export declare function contains(element: Element, child: Node): boolean;
export declare function display(element: HTMLElement, display?: boolean): void;
export declare function undisplay(element: HTMLElement): void;
export declare function show(element: HTMLElement): void;
export declare function hide(element: HTMLElement): void;
export declare function offset_bbox(element: Element): BBox;
export declare function parent(el: HTMLElement, selector: string): HTMLElement | null;
export type ElementExtents = {
    border: Extents;
    margin: Extents;
    padding: Extents;
};
export declare function extents(el: HTMLElement): ElementExtents;
export declare function size(el: HTMLElement): Size;
export declare function scroll_size(el: HTMLElement): Size;
export declare function outer_size(el: HTMLElement): Size;
export declare function content_size(el: HTMLElement): Size;
export declare function bounding_box(el: Element): BBox;
export declare function position(el: HTMLElement, box: Box, margin?: Extents): void;
export declare class ClassList {
    private readonly class_list;
    constructor(class_list: DOMTokenList);
    get values(): string[];
    has(cls: string): boolean;
    add(...classes: string[]): this;
    remove(...classes: string[] | string[][]): this;
    clear(): this;
    toggle(cls: string, activate?: boolean): this;
}
export declare function classes(el: HTMLElement): ClassList;
export declare function toggle_attribute(el: HTMLElement, attr: string, state?: boolean): void;
type WhitespaceKeys = "Tab" | "Enter" | " ";
type UIKeys = "Escape";
type NavigationKeys = "Home" | "End" | "PageUp" | "PageDown" | "ArrowLeft" | "ArrowRight" | "ArrowUp" | "ArrowDown";
type EditingKeys = "Backspace" | "Delete";
export type Keys = WhitespaceKeys | UIKeys | NavigationKeys | EditingKeys;
export declare enum MouseButton {
    None = 0,
    Primary = 1,
    Secondary = 2,
    Auxiliary = 4,
    Left = 1,
    Right = 2,
    Middle = 4
}
import { CSSOurStyles } from "./css";
export declare abstract class StyleSheet {
    protected readonly el: HTMLStyleElement | HTMLLinkElement;
    install(el: HTMLElement | ShadowRoot): void;
    uninstall(): void;
}
export declare class InlineStyleSheet extends StyleSheet {
    protected readonly el: HTMLStyleElement;
    constructor(css?: string);
    clear(): void;
    private _to_rules;
    private _to_css;
    replace(css: string, styles?: CSSOurStyles): void;
    prepend(css: string, styles?: CSSOurStyles): void;
    append(css: string, styles?: CSSOurStyles): void;
    remove(): void;
}
export declare class GlobalInlineStyleSheet extends InlineStyleSheet {
    install(): void;
}
export declare class ImportedStyleSheet extends StyleSheet {
    protected readonly el: HTMLLinkElement;
    constructor(url: string);
    replace(url: string): void;
    remove(): void;
}
export declare class GlobalImportedStyleSheet extends ImportedStyleSheet {
    install(): void;
}
export type StyleSheetLike = StyleSheet | string;
export declare function dom_ready(): Promise<void>;
export declare function px(value: number): string;
export declare const supports_adopted_stylesheets: boolean;
//# sourceMappingURL=dom.d.ts.map