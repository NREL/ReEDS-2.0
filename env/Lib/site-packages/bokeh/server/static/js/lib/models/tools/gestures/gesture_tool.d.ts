import { Tool, ToolView } from "../tool";
import { OnOffButton } from "../on_off_button";
import { PlotView } from "../../plots/plot";
import { EventType } from "../../../core/ui_events";
import * as p from "../../../core/properties";
export declare abstract class GestureToolView extends ToolView {
    model: GestureTool;
    readonly parent: PlotView;
    get plot_view(): PlotView;
}
export declare namespace GestureTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = Tool.Props;
}
export interface GestureTool extends GestureTool.Attrs {
}
export declare abstract class GestureTool extends Tool {
    properties: GestureTool.Props;
    __view_type__: GestureToolView;
    constructor(attrs?: Partial<GestureTool.Attrs>);
    abstract readonly default_order: number;
    abstract readonly event_type: EventType | EventType[];
    tool_button(): OnOffButton;
}
//# sourceMappingURL=gesture_tool.d.ts.map