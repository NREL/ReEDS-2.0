import { DOMNode, DOMNodeView } from "./dom_node";
import { UIElement } from "../ui/ui_element";
import { ViewStorage, IterViews } from "../../core/build_views";
import * as p from "../../core/properties";
export declare class HTMLView extends DOMNodeView {
    model: HTML;
    el: HTMLElement;
    protected readonly _refs: ViewStorage<DOMNode | UIElement>;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    remove(): void;
    render(): void;
}
export declare namespace HTML {
    type Attrs = p.AttrsOf<Props>;
    type Props = DOMNode.Props & {
        html: p.Property<string | (string | DOMNode | UIElement)[]>;
        refs: p.Property<(DOMNode | UIElement)[]>;
    };
}
export interface HTML extends HTML.Attrs {
}
export declare class HTML extends DOMNode {
    properties: HTML.Props;
    __view_type__: HTMLView;
    constructor(attrs?: Partial<HTML.Attrs>);
}
//# sourceMappingURL=html.d.ts.map