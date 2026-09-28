import { houseFrom } from './zodiac.ts';
import type { MangalDoshaResult, MangalInput, MangalPlacement, MangalReference, MangalRuleset } from './types.ts';

/* Structural Mangal / Kuja Dosha evaluation on the four signs the rule needs.
 *
 * A provider may return only "dosha or not". Mangaly wants to say *why*, so it
 * derives the placements itself from canonical data. The provider's verdict is
 * still asked for and must agree (see the adapter): this layer explains, the
 * provider confirms.
 *
 * Mangal Dosha is never part of the 36-point score. */

export function evaluateMangal(input: MangalInput, ruleset: MangalRuleset): MangalDoshaResult {
  const referenceRashi: Record<MangalReference, number> = {
    LAGNA: input.lagnaRashi,
    MOON: input.moonRashi,
    VENUS: input.venusRashi,
  };

  const placements: MangalPlacement[] = ruleset.referencePoints.map((reference) => {
    const house = houseFrom(referenceRashi[reference], input.marsRashi);
    return { reference, house, inDoshaHouse: ruleset.houses.includes(house) };
  });

  const relevant = placements.filter((p) => p.inDoshaHouse);
  if (relevant.length === 0) {
    return {
      status: 'ABSENT',
      rulesetId: ruleset.id,
      marsRashi: input.marsRashi,
      relevantPlacements: [],
      cancellationApplied: false,
      cancellationCode: null,
      level: null,
      explanationCode: 'MANGAL.NO_MARS_PLACEMENT_IN_RULE_HOUSES',
    };
  }

  if (ruleset.cancellationMarsRashis.includes(input.marsRashi)) {
    return {
      status: 'CANCELLED',
      rulesetId: ruleset.id,
      marsRashi: input.marsRashi,
      relevantPlacements: relevant,
      cancellationApplied: true,
      cancellationCode: 'MARS_IN_OWN_OR_EXALTED_SIGN',
      level: null,
      explanationCode: 'MANGAL.PLACEMENT_CANCELLED_MARS_OWN_OR_EXALTED_SIGN',
    };
  }

  return {
    status: 'PRESENT',
    rulesetId: ruleset.id,
    marsRashi: input.marsRashi,
    relevantPlacements: relevant,
    cancellationApplied: false,
    cancellationCode: null,
    level: ruleset.highFromReferences === undefined ? null : relevant.length >= ruleset.highFromReferences ? 'HIGH' : 'LOW',
    explanationCode: 'MANGAL.MARS_IN_RULE_HOUSE',
  };
}

export function indeterminateMangal(ruleset: MangalRuleset): MangalDoshaResult {
  return {
    status: 'INDETERMINATE',
    rulesetId: ruleset.id,
    marsRashi: null,
    relevantPlacements: [],
    cancellationApplied: false,
    cancellationCode: null,
    level: null,
    explanationCode: 'MANGAL.NOT_DETERMINABLE_FROM_BIRTH_TIME',
  };
}
