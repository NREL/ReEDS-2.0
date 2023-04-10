import { Transform } from "./base";
import { MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import { SingleMarkerGL } from "./single_marker";
import type { RectView } from "../rect";
export declare class RectGL extends SingleMarkerGL {
    readonly glyph: RectView;
    constructor(regl_wrapper: ReglWrapper, glyph: RectView);
    draw(indices: number[], main_glyph: RectView, transform: Transform): void;
    protected _get_visuals(): MarkerVisuals;
    protected _set_data(): void;
}
//# sourceMappingURL=rect.d.ts.map