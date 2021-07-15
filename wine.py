# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields, Model
from trytond.pool import Pool
from trytond.pyson import Bool, Eval
from trytond.transaction import Transaction

__all__ = ['WineMixin']


_DEPENDS = ['agronomic_type']
_WINE_DIGITS = 4


class WineMixin(Model):
    wine_quality_confirm = fields.Date('Quality Confirm', readonly=True)
    wine_quality_success = fields.Boolean('Quality Success', readonly=True, states={
            'invisible': ~Bool(Eval('wine_quality_confirm', None)),
        }, depends=['wine_quality_confirm'])
    wine_quality_comment = fields.Function(fields.Text('Wine Quality Comments'),
        'get_wine_quality_comment')

    wine_likely_alcohol_content = fields.Float('Likely Alcohol Content',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort']
            )}, depends=_DEPENDS)
    wine_likely_alcohol_content_comment = fields.Text('Likely Alcohol Content Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort']
            )}, depends=_DEPENDS)
    wine_likely_alcohol_content_confirm = fields.Date('Likely Alcohol Content Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
             ['grape', 'do-wort', 'not-do-wort']
         )}, depends=_DEPENDS)
    wine_likely_alcohol_content_success = fields.Boolean('Likely Alcohol Content Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
            ['grape', 'do-wort', 'not-do-wort']
        )}, depends=_DEPENDS)


    wine_botrytis = fields.Float('Botrytis',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine']
            )}, depends=_DEPENDS)
    wine_botrytis_comment = fields.Text('Botrytis Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine']
            )}, depends=_DEPENDS)
    wine_botrytis_confirm = fields.Date('Botrytis Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine']
         )}, depends=_DEPENDS)
    wine_botrytis_success = fields.Boolean('Botrytis Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine']
        )}, depends=_DEPENDS)

    wine_alcohol_content = fields.Float('Alcohol Content',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_alcohol_content_comment = fields.Text('Alcohol Content Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_alcohol_content_confirm = fields.Date('Alcohol Content Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_alcohol_content_success = fields.Boolean('Alcohol Content Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_density = fields.Float('Density',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine']
            )}, depends=_DEPENDS)
    wine_density_comment = fields.Text('Density Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine']
            )}, depends=_DEPENDS)
    wine_density_confirm = fields.Date('Density Comment Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine']
         )}, depends=_DEPENDS)
    wine_density_success = fields.Boolean('Density Comment Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine']
        )}, depends=_DEPENDS)

    wine_temperature = fields.Float('Temperature',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'filtered-wine']
            )}, depends=_DEPENDS)
    wine_temperature_comment = fields.Text('Temperature Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'filtered-wine']
            )}, depends=_DEPENDS)
    wine_temperature_confirm = fields.Date('Temperature Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'filtered-wine']
         )}, depends=_DEPENDS)
    wine_temperature_success = fields.Boolean('Temperature Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'filtered-wine']
        )}, depends=_DEPENDS)

    wine_ph = fields.Float('PH',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_ph_comment = fields.Text('PH Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_ph_confirm = fields.Date('PH Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_ph_success= fields.Boolean('PH Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_free_sulphur = fields.Float('Free Sulphur',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_free_sulphur_comment = fields.Text('Free Sulphur Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_free_sulphur_confirm = fields.Date('Free Sulphur Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_free_sulphur_success = fields.Boolean('Free Sulphur Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_total_sulphur = fields.Float('Total Sulphur',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_total_sulphur_comment = fields.Text('Total Sulphur Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_total_sulphur_confirm = fields.Date('Total Sulphur Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_total_sulphur_success = fields.Boolean('Total Sulphur Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_tartaric_acidity = fields.Float('Tartaric Acidity',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tartaric_acidity_comment = fields.Text('Tartaric Acidity Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tartaric_acidity_confirm = fields.Date('Tartaric Acidity Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_tartaric_acidity_success = fields.Boolean('Tartaric Acidity Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_volatility = fields.Float('Volatility',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_volatility_comment = fields.Text('Volatility Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_volatility_confirm = fields.Date('Volatility Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_volatility_success = fields.Boolean('Volatility Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_malic_acid = fields.Float('Malic Acid',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
            )}, depends=_DEPENDS)
    wine_malic_acid_comment = fields.Text('Malic Acid Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
            )}, depends=_DEPENDS)
    wine_malic_acid_confirm = fields.Date('Malic Acid Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
         )}, depends=_DEPENDS)
    wine_malic_acid_success = fields.Boolean('Malic Acid Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
        )}, depends=_DEPENDS)

    wine_lactic_acid = fields.Float('Lactic Acid',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
            )}, depends=_DEPENDS)
    wine_lactic_acid_comment = fields.Text('Lactic Acid Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
            )}, depends=_DEPENDS)
    wine_lactic_acid_confirm = fields.Date('Lactic Acid Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
         )}, depends=_DEPENDS)
    wine_lactic_acid_success = fields.Boolean('Lactic Acid Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine']
        )}, depends=_DEPENDS)

    wine_protein_stability = fields.Float('Protein Stability',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_protein_stability_comment = fields.Text('Protein Stability Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_protein_stability_confirm = fields.Date('Protein Stability Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_protein_stability_success = fields.Boolean('Protein Stability Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_tartaric_stability = fields.Float('Tartaric Stability',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tartaric_stability_comment = fields.Text('Tartaric Stability Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tartaric_stability_confirm = fields.Date('Tartaric Stability Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_tartaric_stability_success = fields.Boolean('Tartaric Stability Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_turbidity = fields.Float('Turbidity',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
            )}, depends=_DEPENDS)
    wine_turbidity_comment = fields.Text('Turbidity Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
            )}, depends=_DEPENDS)
    wine_turbidity_confirm = fields.Date('Turbidity Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
         )}, depends=_DEPENDS)
    wine_turbidity_success = fields.Boolean('Turbidity Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
        )}, depends=_DEPENDS)

    wine_glucose_fructose = fields.Float('Glucose/Fructose',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_glucose_fructose_comment = fields.Text('Glucose/Fructose Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_glucose_fructose_confirm = fields.Date('Glucose/Fructose Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_glucose_fructose_success = fields.Boolean('Glucose/Fructose Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_color_intensity = fields.Float('Color Intensity',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_color_intensity_comment = fields.Text('Color Intensity Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_color_intensity_confirm = fields.Date('Color Intensity Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_color_intensity_success = fields.Boolean('Color Intensity Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_tone = fields.Float('Tone',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tone_comment = fields.Text('Tone Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tone_confirm = fields.Date('Tone Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_tone_success = fields.Boolean('Tone Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_clogging = fields.Float('Clogging',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
            )}, depends=_DEPENDS)
    wine_clogging_comment = fields.Text('Clogging Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
            )}, depends=_DEPENDS)
    wine_clogging_confirm = fields.Date('Clogging Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
         )}, depends=_DEPENDS)
    wine_clogging_success = fields.Boolean('Clogging Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['filtered-wine']
        )}, depends=_DEPENDS)

    wine_overall_impression = fields.Float('Overall Impression',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_overall_impression_comment = fields.Text('Overall Impression Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_overall_impression_confirm = fields.Date('Overall Impression Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_overall_impression_success = fields.Boolean('Overall Impression Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['grape', 'do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_observing_phase = fields.Float('Observing Phase',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_observing_phase_comment = fields.Text('Observing Phase Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_observing_phase_confirm = fields.Date('Observing Phase Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_observing_phase_success = fields.Boolean('Observing Phase Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_smelling_phase = fields.Float('Smelling Phase',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_smelling_phase_comment = fields.Text('Smelling Phase Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_smelling_phase_confirm = fields.Date('Smelling Phase Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_smelling_phase_success = fields.Boolean('Smelling Phase Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    wine_tasting_phase = fields.Float('Tasting Phase',
        digits=(16, _WINE_DIGITS), readonly=True, states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tasting_phase_comment = fields.Text('Tasting Phase Comment',
        states={
            'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
            )}, depends=_DEPENDS)
    wine_tasting_phase_confirm = fields.Date('Tasting Phase Confirm', readonly=True, states={
         'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
         )}, depends=_DEPENDS)
    wine_tasting_phase_success = fields.Boolean('Tasting Phase Success', readonly=True, states={
        'invisible': ~Eval('agronomic_type').in_(
                ['do-wort', 'not-do-wort', 'unfiltered-wine', 'clarified-wine', 'filtered-wine', 'bottled-wine']
        )}, depends=_DEPENDS)

    @classmethod
    def get_wine_quality_comment(cls, records, name):
        pool = Pool()
        Translation = pool.get('ir.translation')

        res = dict((x.id, None) for x in records)
        language = Transaction().language

        for record in records:
            data = ''
            for key in cls._fields.keys():
                if (key.startswith('wine_') and key.endswith('_comment')
                        and key != 'wine_quality_comment'):
                    if not getattr(record, key):
                        continue
                    field_name = '%s,%s' % (cls.__name__, key)
                    label = (Translation.get_source(field_name, 'field', language)
                        or getattr(cls, key).string)
                    data += '<div><b>%s</b><br/>%s</div>' % (label, getattr(record, key))
            res[record.id] = data

        return res
