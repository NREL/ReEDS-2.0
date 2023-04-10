import { GestureTool, GestureToolView } from "./gesture_tool";
import * as p from "../../../core/properties";
import { PinchEvent, ScrollEvent } from "../../../core/ui_events";
import { Dimensions } from "../../../core/enums";
export declare class WheelZoomToolView extends GestureToolView {
    model: WheelZoomTool;
    _pinch(ev: PinchEvent): void;
    _scroll(ev: ScrollEvent): void;
}
export declare namespace WheelZoomTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = GestureTool.Props & {
        dimensions: p.Property<Dimensions>;
        maintain_focus: p.Property<boolean>;
        zoom_on_axis: p.Property<boolean>;
        speed: p.Property<number>;
    };
}
export interface WheelZoomTool extends WheelZoomTool.Attrs {
}
export declare class WheelZoomTool extends GestureTool {
    properties: WheelZoomTool.Props;
    __view_type__: WheelZoomToolView;
    constructor(attrs?: Partial<WheelZoomTool.Attrs>);
    tool_name: string;
    tool_icon: string;
    event_type: "pinch" | "scroll";
    default_order: number;
    get tooltip(): string;
}
//# sourceMappingURL=wheel_zoom_tool.d.ts.map