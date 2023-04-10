import { Model } from "../../model";
import { Styles } from "../dom/styles";
import { StyleSheet as BaseStyleSheet } from "../dom/stylesheets";
import { Align } from "../../core/enums";
import { SizingPolicy } from "../../core/layout";
import { DOMComponentView } from "../../core/dom_view";
import { SerializableState } from "../../core/view";
import { CSSStyles, StyleSheet, InlineStyleSheet, StyleSheetLike } from "../../core/dom";
import { CanvasLayer } from "../../core/util/canvas";
import { BBox } from "../../core/util/bbox";
import * as p from "../../core/properties";
export type DOMBoxSizing = {
    width_policy: SizingPolicy | "auto";
    height_policy: SizingPolicy | "auto";
    width: number | null;
    height: number | null;
    aspect_ratio: number | "auto" | null;
    halign?: Align;
    valign?: Align;
};
export declare abstract class UIElementView extends DOMComponentView {
    model: UIElement;
    protected readonly _display: InlineStyleSheet;
    readonly style: InlineStyleSheet;
    protected _css_classes(): Iterable<string>;
    protected _stylesheets(): Iterable<StyleSheet>;
    protected _computed_stylesheets(): Iterable<StyleSheet>;
    stylesheets(): StyleSheetLike[];
    update_style(): void;
    box_sizing(): DOMBoxSizing;
    private _bbox;
    get bbox(): BBox;
    update_bbox(): boolean;
    protected _update_bbox(): boolean;
    protected _resize_observer: ResizeObserver;
    initialize(): void;
    connect_signals(): void;
    remove(): void;
    protected _after_resize(): void;
    after_resize(): void;
    render_to(element: Node): void;
    render(): void;
    protected _after_render(): void;
    after_render(): void;
    private _is_displayed;
    get is_displayed(): boolean;
    protected _apply_visible(): void;
    protected _apply_styles(): void;
    protected _update_visible(): void;
    protected _update_styles(): void;
    export(type?: "auto" | "png" | "svg", hidpi?: boolean): CanvasLayer;
    serializable_state(): SerializableState;
}
export declare namespace UIElement {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        visible: p.Property<boolean>;
        css_classes: p.Property<string[]>;
        styles: p.Property<CSSStyles | Styles>;
        stylesheets: p.Property<(BaseStyleSheet | string | {
            [key: string]: CSSStyles | Styles;
        })[]>;
    };
}
export interface UIElement extends UIElement.Attrs {
}
export declare abstract class UIElement extends Model {
    properties: UIElement.Props;
    __view_type__: UIElementView;
    constructor(attrs?: Partial<UIElement.Attrs>);
}
//# sourceMappingURL=ui_element.d.ts.map