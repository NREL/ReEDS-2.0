import { Anchor, TextAnchor, BorderRadius, Padding } from "./kinds";
import { TextAlign, TextBaseline } from "../../core/enums";
import { XY, LRTB, Corners } from "../../core/util/bbox";
export declare function anchor(anchor: Anchor): XY<number>;
export declare function text_anchor(text_anchor: TextAnchor, align: TextAlign, baseline: TextBaseline): XY<number>;
export declare function padding(padding: Padding): LRTB<number>;
export declare function border_radius(border_radius: BorderRadius): Corners<number>;
//# sourceMappingURL=resolve.d.ts.map