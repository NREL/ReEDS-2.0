import { LayoutDOM, LayoutDOMView, FullDisplay } from "./layout_dom";
import { UIElement } from "../ui/ui_element";
import { TracksSizing, GridSpacing } from "../common/kinds";
import * as p from "../../core/properties";
export declare abstract class CSSGridBoxView extends LayoutDOMView {
    model: CSSGridBox;
    connect_signals(): void;
    get child_models(): UIElement[];
    protected _intrinsic_display(): FullDisplay;
    protected abstract get _children(): [UIElement, number, number, number?, number?][];
    protected abstract get _rows(): TracksSizing | null;
    protected abstract get _cols(): TracksSizing | null;
    _update_layout(): void;
}
export declare namespace CSSGridBox {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutDOM.Props & {
        spacing: p.Property<GridSpacing>;
    };
}
export interface CSSGridBox extends CSSGridBox.Attrs {
}
export declare abstract class CSSGridBox extends LayoutDOM {
    properties: CSSGridBox.Props;
    __view_type__: CSSGridBoxView;
    constructor(attrs?: Partial<CSSGridBox.Attrs>);
}
//# sourceMappingURL=css_grid_box.d.ts.map