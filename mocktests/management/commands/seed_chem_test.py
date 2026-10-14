from django.core.management.base import BaseCommand
from django.db import transaction
from mocktests.models import Mock_Test, Question


class Command(BaseCommand):
    help = 'Seeds the database with the EPD ISA-1 Mock Test (Sem 1)'

    def handle(self, *args, **kwargs):
        self.create_epd_test()

    def _bulk_create_questions(self, test, questions_data):
        objs = [
            Question(
                test=test,
                question_desc=q['desc'],
                question_image=q.get('image', '') or None,
                option_a=q['a'], option_b=q['b'],
                option_c=q['c'], option_d=q['d'],
                correct_answer=q['ans'],
                marks=q['marks'],
                explanation=q['exp'],
            )
            for q in questions_data
        ]
        Question.objects.bulk_create(objs)
        total = sum(q['marks'] for q in questions_data)
        one = sum(1 for q in questions_data if q['marks'] == 1)
        two = sum(1 for q in questions_data if q['marks'] == 2)
        img = sum(1 for q in questions_data if q.get('image'))
        self.stdout.write(self.style.SUCCESS(
            f'  -> {len(questions_data)} questions | 1-markers: {one} | '
            f'2-markers: {two} | With image: {img} | Total marks: {total}'
        ))

    @transaction.atomic
    def create_epd_test(self):
        test, created = Mock_Test.objects.get_or_create(
            title="EPD ISA-1 Mock Test",
            defaults={
                'description': (
                    "Electronic Principles and Devices. Unit 1 (Semiconductor Diode) & "
                    "Unit 2 (Diode Applications). 30 questions, 40 marks, 65 minutes."
                ),
                'course_name': "Electronic Principles and Devices",
                'semester': 1,
                'total_qns': 30,
                'duration': 65,
            }
        )
        if not created:
            Question.objects.filter(test=test).delete()
            test.total_qns = 30
            test.duration = 65
            test.semester = 1
            test.save()

        self.stdout.write(self.style.SUCCESS(f'Creating Questions for "{test.title}"...'))

        questions_data = [
            # ==================================================
            # 2-MARKERS (10 total — 5 Unit 1, 5 Unit 2)
            # ==================================================
            # ISA Q1.a — diode voltage numerical
            {
                'desc': (
                    'Given a diode current of 16 mA, V_T = 26 mV, n = 1, and I_S = 1 nA, '
                    'find the applied voltage V_D.'
                ),
                'a': '0.431 V', 'b': '0.215 V', 'c': '0.862 V', 'd': '1.204 V',
                'ans': 'A', 'marks': 2,
                'exp': 'I_D = I_S(e^(V_D/nV_T) − 1) → 16 mA = 1 nA(e^(V_D/26mV) − 1) → 16×10⁶ = e^(V_D/26mV) → V_D/26mV = 16.5881 → V_D = 0.431 V.'
            },
            # ISA Q1.b — clipper (image-based)
            {
                'desc': (
                    'In the following clipper circuit, find the transition voltage (assume ideal diode).'
                ),
                'image': 'question_images/isa_q1b_clipper.png',
                'a': '4 V', 'b': '8 V', 'c': '0 V', 'd': '−4 V',
                'ans': 'A', 'marks': 2,
                'exp': 'The transition voltage is 4 V (from the source in series with the diode).'
            },
            # ISA Q1.c — shunt capacitor filter with CT-FWR (image-based)
            {
                'desc': (
                    'For the shunt capacitor filter used with a centre tap full wave rectifier shown '
                    'below, what is the working principle during the positive half cycle?'
                ),
                'image': 'question_images/isa_q1c_filter.png',
                'a': 'D1 is forward biased, capacitor charges to Vm, then discharges through RL',
                'b': 'D2 is forward biased, capacitor charges to Vm, then discharges through RL',
                'c': 'Both D1 and D2 are reverse biased, capacitor discharges through RL',
                'd': 'Capacitor discharges fully to 0 V before next half cycle',
                'ans': 'A', 'marks': 2,
                'exp': 'During the positive half cycle, D1 is forward biased in the centre tap FWR. The capacitor charges to Vm then discharges through RL, keeping output nearly constant.'
            },
            # ISA Q1.d — half-wave rectifier Vm calculation (image-based)
            {
                'desc': (
                    'For the half-wave rectifier with silicon diode (V_k = 0.7 V) shown below, '
                    'V_dc = 2 V. What is the peak input voltage V_m?'
                ),
                'image': 'question_images/isa_q1d_hwr.png',
                'a': '6.98 V', 'b': '2 V', 'c': '6.28 V', 'd': '5.6 V',
                'ans': 'A', 'marks': 2,
                'exp': 'V_dc ≈ 0.318(V_m − V_k) → 2 = 0.318(V_m − 0.7) → V_m = 6.98 V.'
            },
            # ISA Q6 — parallel bias clipper (image-based)
            {
                'desc': (
                    'In the parallel bias clipper shown below, assume the ideal diode is turned ON. '
                    'What is the output voltage V_o?'
                ),
                'image': 'question_images/isa_q6_clipper.png',
                'a': '4 V', 'b': '8 V', 'c': '−4 V', 'd': '0 V',
                'ans': 'A', 'marks': 2,
                'exp': 'When the diode is ON, the output is clamped directly across the 4 V supply.'
            },
            # ISA Q9 — two-diode circuit (image-based)
            {
                'desc': (
                    'Determine V_0 for the following circuit with two silicon diodes.'
                ),
                'image': 'question_images/isa_q9_two_diode.png',
                'a': '−4.3 V', 'b': '−5 V', 'c': '0.7 V', 'd': '−5.7 V',
                'ans': 'A', 'marks': 2,
                'exp': 'The Si diode with −5 V at cathode is ON, the other is OFF. V_0 = −5 V + 0.7 V = −4.3 V.'
            },
            # ISA Q7 — parallel diode output (image-based)
            {
                'desc': (
                    'In the parallel diode circuit shown below, what is the output voltage V_o?'
                ),
                'image': 'question_images/isa_q7_parallel.png',
                'a': '0.7 V', 'b': '10 V', 'c': '9.3 V', 'd': '0 V',
                'ans': 'A', 'marks': 2,
                'exp': 'Diodes in parallel are forward biased; output is clamped to the knee voltage of Si, V_o = 0.7 V.'
            },
            # ISA Q11 — series diode V_D (image-based)
            {
                'desc': (
                    'For the series diode configuration shown below with +0.5 V applied, '
                    'determine V_D.'
                ),
                'image': 'question_images/isa_q11_series.png',
                'a': '0.5 V', 'b': '0.7 V', 'c': '0 V', 'd': '1.2 V',
                'ans': 'A', 'marks': 2,
                'exp': 'Applied voltage 0.5 V < knee voltage 0.7 V, so diode is OFF. Voltage across diode V_D = 0.5 V.'
            },
            # ISA Q12 — LED polarity detector R (image-based)
            {
                'desc': (
                    'In the LED polarity detector shown below, find R to ensure 20 mA through the '
                    'on diode. Assume V_LED = 2 V, +8 V source.'
                ),
                'image': 'question_images/isa_q12_led.png',
                'a': '300 Ω', 'b': '400 Ω', 'c': '200 Ω', 'd': '500 Ω',
                'ans': 'A', 'marks': 2,
                'exp': 'I = (E − V_LED)/R = (8 − 2)/R = 20 mA → R = 6V/20mA = 300 Ω.'
            },
            # ISA Q14 — capacitor voltage V_C (image-based)
            {
                'desc': (
                    'In the following circuit, find the capacitor voltage V_C. Assume ideal diode '
                    'and V1 = 0.5 V.'
                ),
                'image': 'question_images/isa_q14_cap.png',
                'a': '1.5 V', 'b': '2 V', 'c': '0.5 V', 'd': '1 V',
                'ans': 'A', 'marks': 2,
                'exp': 'V_C = 1.5 V.'
            },

            # ==================================================
            # 1-MARKERS (20 total — 10 Unit 1, 10 Unit 2)
            # ==================================================
            # Unit 1: thermal voltage
            {
                'desc': 'The thermal voltage V_T of a diode at room temperature (300 K) is approximately:',
                'a': '25.9 mV', 'b': '12.5 mV', 'c': '50 mV', 'd': '100 mV',
                'ans': 'A', 'marks': 1,
                'exp': 'V_T = kT/q = (1.38×10⁻²³ × 300)/(1.6×10⁻¹⁹) = 25.875 mV ≈ 26 mV.'
            },
            # Unit 1: semiconductor materials
            {
                'desc': 'Which of the following is NOT a semiconductor material used in electronic devices?',
                'a': 'Silicon', 'b': 'Germanium', 'c': 'Gallium Arsenide', 'd': 'Aluminium',
                'ans': 'D', 'marks': 1,
                'exp': 'Ge, Si, and GaAs are the three most common semiconductor materials. Aluminium is a conductor.'
            },
            # Unit 1: n-type doping
            {
                'desc': 'An n-type semiconductor is formed by doping with:',
                'a': 'Pentavalent impurities', 'b': 'Trivalent impurities',
                'c': 'Tetravalent impurities', 'd': 'Hexavalent impurities',
                'ans': 'A', 'marks': 1,
                'exp': 'n-type is created by introducing pentavalent impurities (antimony, arsenic, phosphorus).'
            },
            # Unit 1: depletion region
            {
                'desc': (
                    'In an unbiased p-n junction, the region near the junction that is depleted '
                    'of free carriers is called:'
                ),
                'a': 'Depletion region', 'b': 'Neutral region',
                'c': 'Conduction region', 'd': 'Valence region',
                'ans': 'A', 'marks': 1,
                'exp': 'The region of uncovered positive and negative ions is called the depletion region.'
            },
            # Unit 1: barrier voltage temperature coefficient
            {
                'desc': 'The barrier voltage of a silicon diode decreases by how much for every 1°C rise in temperature?',
                'a': '2.5 mV/°C', 'b': '5 mV/°C', 'c': '1.5 mV/°C', 'd': '0.5 mV/°C',
                'ans': 'A', 'marks': 1,
                'exp': 'Barrier voltage decreases by 2.5 mV/°C rise in temperature for both Ge and Si.'
            },
            # Unit 1: I_S doubling
            {
                'desc': 'The reverse saturation current of a diode approximately doubles for every:',
                'a': '10 °C rise in temperature', 'b': '5 °C rise in temperature',
                'c': '20 °C rise in temperature', 'd': '1 °C rise in temperature',
                'ans': 'A', 'marks': 1,
                'exp': 'Reverse saturation current approximately doubles for every 10 °C rise in temperature.'
            },
            # Unit 1: AC resistance range
            {
                'desc': 'The AC or dynamic resistance of a diode in the active region typically ranges from:',
                'a': '1 Ω to 100 Ω', 'b': '10 kΩ to 100 kΩ',
                'c': '1 MΩ to 10 MΩ', 'd': '0.1 Ω to 1 Ω',
                'ans': 'A', 'marks': 1,
                'exp': 'AC resistance in the active region typically ranges from 1 Ω to 100 Ω.'
            },
            # Unit 1: Shockley equation form
            {
                'desc': "Identify the correct Shockley's current equation.",
                'a': 'I_D = I_S e^((V_D/nV_T) − 1)', 'b': 'I_D = I_S(e^(V_D/nV_T) − 1)',
                'c': 'I_D = I_S(e^(nV_T/V_D) − 1)', 'd': 'I_D = I_S(e^(V_D/V_T) + 1)',
                'ans': 'B', 'marks': 1,
                'exp': "Shockley's equation: I_D = I_S(e^(V_D/nV_T) − 1)."
            },
            # Unit 1: Zener breakdown doping
            {
                'desc': 'Zener breakdown occurs in diodes that are:',
                'a': 'Highly doped', 'b': 'Lightly doped',
                'c': 'Not doped', 'd': 'Moderately doped',
                'ans': 'A', 'marks': 1,
                'exp': 'Zener breakdown occurs in highly doped diodes with a narrow depletion region.'
            },
            # Unit 1: ideal diode drop
            {
                'desc': 'Drop across an ideal diode when it is forward biased is:',
                'a': '0 V', 'b': '0.7 V', 'c': '0.3 V', 'd': '1.2 V',
                'ans': 'A', 'marks': 1,
                'exp': 'An ideal diode acts as a closed switch with zero voltage drop when forward biased.'
            },
            # Unit 2: Zener depletion narrow
            {
                'desc': 'Zener diodes are usually heavily doped diodes, hence the depletion layer is:',
                'a': 'Very narrow', 'b': 'Very wide', 'c': 'Moderately wide', 'd': 'Zero',
                'ans': 'A', 'marks': 1,
                'exp': 'Heavy doping makes the depletion layer very narrow.'
            },
            # Unit 2: Zener incorrect condition
            {
                'desc': 'In a Zener voltage regulator, which of the following is an INCORRECT condition?',
                'a': 'Vin should be lesser than Vz', 'b': 'Vin should be greater than Vz',
                'c': 'Iz should be greater than Izmin', 'd': 'Iz should be less than or equal to Izmax',
                'ans': 'A', 'marks': 1,
                'exp': 'Vin must be greater than Vz for the Zener to operate in the breakdown region.'
            },
            # Unit 2: Zener I_Zmax
            {
                'desc': 'For a Zener regulator with V_Z = 14 V and P_max = 400 mW, the maximum Zener current I_Zmax is:',
                'a': '28.57 mA', 'b': '14.28 mA', 'c': '57.14 mA', 'd': '7.14 mA',
                'ans': 'A', 'marks': 1,
                'exp': 'I_Zmax = P_max / V_Z = 400 mW / 14 V = 28.57 mA.'
            },
            # Unit 2: ripple factor values
            {
                'desc': 'The ripple factor of a Half Wave Rectifier (ideal) and Full Wave Rectifier (ideal) respectively are:',
                'a': '1.21 and 0.48', 'b': '0.48 and 1.21',
                'c': '1.0 and 0.5', 'd': '0.81 and 0.81',
                'ans': 'A', 'marks': 1,
                'exp': 'Ripple factor of HWR is 1.21; FWR is 0.48.'
            },
            # Unit 2: diode count in rectifiers
            {
                'desc': 'How many diodes are required for a Bridge Full Wave Rectifier and a Center Tap Full Wave Rectifier respectively?',
                'a': '4 and 2', 'b': '2 and 4', 'c': '1 and 2', 'd': '4 and 1',
                'ans': 'A', 'marks': 1,
                'exp': 'Bridge FWR requires 4 diodes. Center Tap FWR requires 2 diodes.'
            },
            # Unit 2: shunt capacitor placement
            {
                'desc': 'In a shunt capacitor filter, the capacitor is connected:',
                'a': 'In parallel with the load', 'b': 'In series with the load',
                'c': 'In series with the diode', 'd': 'Across the transformer',
                'ans': 'A', 'marks': 1,
                'exp': 'Shunt capacitor filter places C in parallel with the load R_L.'
            },
            # Unit 2: regulated PS block
            {
                'desc': 'In a regulated power supply, which block converts AC to pulsating DC?',
                'a': 'Rectifier', 'b': 'Transformer', 'c': 'Filter', 'd': 'Regulator',
                'ans': 'A', 'marks': 1,
                'exp': 'The rectifier converts AC to pulsating DC.'
            },
            # Unit 2: clipper purpose
            {
                'desc': 'A clipper circuit is used to:',
                'a': 'Remove a portion of the input waveform', 'b': 'Shift the DC level of the waveform',
                'c': 'Amplify the input signal', 'd': 'Rectify the AC signal',
                'ans': 'A', 'marks': 1,
                'exp': 'Clippers remove a portion of the input waveform above or below a reference level.'
            },
            # Unit 2: clamper purpose
            {
                'desc': 'A clamper circuit is used to:',
                'a': 'Shift the DC level of a waveform without altering its shape',
                'b': 'Remove a portion of the input waveform',
                'c': 'Amplify the input signal',
                'd': 'Convert AC to DC',
                'ans': 'A', 'marks': 1,
                'exp': 'Clampers shift the DC level of a waveform without changing its shape. Also called DC restorers.'
            },
            # Unit 2: clamper component
            {
                'desc': 'Which component is essential in a clamper circuit to store the DC level?',
                'a': 'Capacitor', 'b': 'Inductor', 'c': 'Resistor', 'd': 'Transformer',
                'ans': 'A', 'marks': 1,
                'exp': 'A capacitor stores the DC level in a clamper circuit.'
            },
        ]

        self._bulk_create_questions(test, questions_data)