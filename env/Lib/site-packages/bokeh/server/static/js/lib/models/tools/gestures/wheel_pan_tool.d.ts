import { GestureTool, GestureToolView } from "./gesture_tool";
import * as p from "../../../core/properties";
import { ScrollEvent } from "../../../core/ui_events";
import { Dimension } from "../../../core/enums";
export declare class WheelPanToolView extends GestureToolView {
    model: WheelPanTool;
    _scroll(ev: ScrollEvent): void;
    _update_ranges(factor: number): void;
}
export declare namespace WheelPanTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = GestureTool.Props & {
        dimension: p.Property<Dimension>;
        speed: p.Property<number>;
    };
}
export interface WheelPanTool extends WheelPanTool.Attrs {
}
export declare class WheelPanTool extends GestureTool {
    properties: WheelPanTool.Props;
    __view_type__: WheelPanToolView;
    constructor(attrs?: Partial<WheelPanTool.Attrs>);
    tool_name: string;
    tool_icon: string;
    event_type: "scroll";
    default_order: number;
    get tooltip(): string;
}
//# sourceMappingURL=wheel_pan_tool.d.ts.map