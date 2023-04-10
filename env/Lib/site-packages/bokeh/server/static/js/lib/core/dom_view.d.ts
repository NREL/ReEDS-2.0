import { View } from "./view";
import { StyleSheet, StyleSheetLike, ClassList } from "./dom";
export interface DOMView extends View {
    constructor: Function & {
        tag_name: keyof HTMLElementTagNameMap;
    };
}
export declare abstract class DOMView extends View {
    parent: DOMView | null;
    static tag_name: keyof HTMLElementTagNameMap;
    el: Node;
    shadow_el?: ShadowRoot;
    get children_el(): Node;
    initialize(): void;
    remove(): void;
    stylesheets(): StyleSheetLike[];
    css_classes(): string[];
    abstract render(): void;
    render_to(element: Node): void;
    finish(): void;
    protected _createElement(): this["el"];
}
export declare abstract class DOMElementView extends DOMView {
    el: HTMLElement;
    class_list: ClassList;
    initialize(): void;
}
export declare abstract class DOMComponentView extends DOMElementView {
    parent: DOMElementView | null;
    readonly root: DOMComponentView;
    shadow_el: ShadowRoot;
    initialize(): void;
    stylesheets(): StyleSheetLike[];
    empty(): void;
    render(): void;
    protected _stylesheets(): Iterable<StyleSheet>;
    protected _css_classes(): Iterable<string>;
    protected _applied_stylesheets: StyleSheet[];
    protected _apply_stylesheets(stylesheets: StyleSheet[]): void;
    protected _applied_css_classes: string[];
    protected _apply_css_classes(classes: string[]): void;
    protected _update_stylesheets(): void;
    protected _update_css_classes(): void;
}
//# sourceMappingURL=dom_view.d.ts.map