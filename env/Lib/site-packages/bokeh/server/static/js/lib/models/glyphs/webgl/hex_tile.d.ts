import { Transform } from "./base";
import { MarkerVisuals } from "./base_marker";
import { ReglWrapper } from "./regl_wrap";
import { SingleMarkerGL } from "./single_marker";
import type { HexTileView } from "../hex_tile";
export declare class HexTileGL extends SingleMarkerGL {
    readonly glyph: HexTileView;
    constructor(regl_wrapper: ReglWrapper, glyph: HexTileView);
    draw(indices: number[], main_glyph: HexTileView, transform: Transform): void;
    protected _get_visuals(): MarkerVisuals;
    protected _set_data(): void;
}
//# sourceMappingURL=hex_tile.d.ts.map