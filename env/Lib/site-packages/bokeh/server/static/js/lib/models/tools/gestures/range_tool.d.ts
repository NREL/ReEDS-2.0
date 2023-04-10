import { Tool, ToolView } from "../tool";
import { OnOffButton } from "../on_off_button";
import { type PlotView } from "../../plots/plot";
import { BoxAnnotation } from "../../annotations/box_annotation";
import { Range1d } from "../../ranges/range1d";
import * as p from "../../../core/properties";
export declare class RangeToolView extends ToolView {
    model: RangeTool;
    readonly parent: PlotView;
    get overlays(): import("../..").Renderer[];
    initialize(): void;
    connect_signals(): void;
}
export declare namespace RangeTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = Tool.Props & {
        x_range: p.Property<Range1d | null>;
        y_range: p.Property<Range1d | null>;
        x_interaction: p.Property<boolean>;
        y_interaction: p.Property<boolean>;
        overlay: p.Property<BoxAnnotation>;
    };
}
export interface RangeTool extends RangeTool.Attrs {
}
export declare class RangeTool extends Tool {
    properties: RangeTool.Props;
    __view_type__: RangeToolView;
    constructor(attrs?: Partial<RangeTool.Attrs>);
    initialize(): void;
    update_ranges_from_overlay(): void;
    update_overlay_from_ranges(): void;
    tool_name: string;
    tool_icon: string;
    tool_button(): OnOffButton;
}
//# sourceMappingURL=range_tool.d.ts.map