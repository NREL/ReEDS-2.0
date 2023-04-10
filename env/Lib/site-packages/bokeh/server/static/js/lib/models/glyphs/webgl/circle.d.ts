import { Transform } from "./base";
import { MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import { SingleMarkerGL } from "./single_marker";
import type { CircleView } from "../circle";
export declare class CircleGL extends SingleMarkerGL {
    readonly glyph: CircleView;
    constructor(regl_wrapper: ReglWrapper, glyph: CircleView);
    draw(indices: number[], main_glyph: CircleView, transform: Transform): void;
    protected _get_visuals(): MarkerVisuals;
    protected _set_data(): void;
}
//# sourceMappingURL=circle.d.ts.map