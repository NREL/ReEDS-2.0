import { Transform } from "./base";
import { MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import { SingleMarkerGL } from "./single_marker";
import type { BlockView } from "../block";
import type { HBarView } from "../hbar";
import type { QuadView } from "../quad";
import type { VBarView } from "../vbar";
type AnyLRTBView = BlockView | HBarView | QuadView | VBarView;
export declare class LRTBGL extends SingleMarkerGL {
    readonly glyph: AnyLRTBView;
    constructor(regl_wrapper: ReglWrapper, glyph: AnyLRTBView);
    draw(indices: number[], main_glyph: AnyLRTBView, transform: Transform): void;
    protected _get_visuals(): MarkerVisuals;
    protected _set_data(): void;
}
export {};
//# sourceMappingURL=lrtb.d.ts.map