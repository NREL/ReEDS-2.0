import { Transform } from "./base";
import { BaseMarkerGL, MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import type { ScatterView } from "../scatter";
import { MarkerType } from "../../../core/enums";
import { Uniform } from "../../../core/uniforms";
export declare class MultiMarkerGL extends BaseMarkerGL {
    readonly glyph: ScatterView;
    protected _marker_types?: Uniform<MarkerType | null>;
    protected _unique_marker_types: (MarkerType | null)[];
    constructor(regl_wrapper: ReglWrapper, glyph: ScatterView);
    draw(indices: number[], main_glyph: ScatterView, transform: Transform): void;
    protected _get_visuals(): MarkerVisuals;
    protected _set_data(): void;
}
//# sourceMappingURL=multi_marker.d.ts.map