import { UIElement, UIElementView } from "./ui_element";
import { ViewStorage, IterViews } from "../../core/build_views";
import { SerializableState } from "../../core/view";
import * as p from "../../core/properties";
export declare class PaneView extends UIElementView {
    model: Pane;
    protected get _ui_elements(): UIElement[];
    protected readonly _child_views: ViewStorage<UIElement>;
    get child_views(): UIElementView[];
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    protected _rebuild_views(): Promise<void>;
    remove(): void;
    connect_signals(): void;
    render(): void;
    has_finished(): boolean;
    serializable_state(): SerializableState;
}
export declare namespace Pane {
    type Attrs = p.AttrsOf<Props>;
    type Props = UIElement.Props & {
        children: p.Property<(string | UIElement)[]>;
    };
}
export interface Pane extends Pane.Attrs {
}
export declare class Pane extends UIElement {
    properties: Pane.Props;
    __view_type__: PaneView;
    constructor(attrs?: Partial<Pane.Attrs>);
}
//# sourceMappingURL=pane.d.ts.map