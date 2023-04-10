import { UIElement, UIElementView } from "./ui_element";
import { Selector } from "../selectors/selector";
import { HTML, HTMLView } from "../dom/html";
import { Anchor, TooltipAttachment } from "../../core/enums";
import { StyleSheetLike } from "../../core/dom";
import { IterViews } from "../../core/build_views";
import * as p from "../../core/properties";
export declare class TooltipView extends UIElementView {
    model: Tooltip;
    protected content_el: HTMLElement;
    protected _observer: ResizeObserver;
    private _target;
    get target(): Element;
    protected _init_target(): void;
    initialize(): void;
    protected _html: HTMLView | null;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    connect_signals(): void;
    remove(): void;
    stylesheets(): StyleSheetLike[];
    get content(): Node;
    render(): void;
    private _anchor_to_align;
    protected _reposition(): void;
}
export declare namespace Tooltip {
    type Attrs = p.AttrsOf<Props>;
    type Props = UIElement.Props & {
        target: p.Property<UIElement | Selector | Node | "auto">;
        position: p.Property<Anchor | [number, number] | null>;
        content: p.Property<string | HTML | Node>;
        attachment: p.Property<TooltipAttachment | "auto">;
        show_arrow: p.Property<boolean>;
        closable: p.Property<boolean>;
        interactive: p.Property<boolean>;
    };
}
export interface Tooltip extends Tooltip.Attrs {
}
export declare class Tooltip extends UIElement {
    properties: Tooltip.Props;
    __view_type__: TooltipView;
    constructor(attrs?: Partial<Tooltip.Attrs>);
    clear(): void;
}
//# sourceMappingURL=tooltip.d.ts.map