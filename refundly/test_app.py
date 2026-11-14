import unittest
from app import analyze, letter
class RulesTest(unittest.TestCase):
    def case(self,**kw):
        d=dict(state='CA',deposit=2200,returned=950,move_in='2022-10-01',move_out='2026-10-01',received='2026-10-20',forwarding=True,itemized=True,deductions=[dict(kind='Painting',amount=650,condition='wear',age=5),dict(kind='Carpet',amount=450,condition='preexisting',age=7),dict(kind='Repair',amount=150,condition='damage',receipt=True)])
        d.update(kw);return d
    def test_example(self):
        r=analyze(self.case());self.assertEqual(r['disputed'],1100);self.assertEqual(r['unaccounted'],0);self.assertEqual(r['deadline'],'2026-10-22')
    def test_letter_excludes_lawful(self):
        d=self.case();text=letter(d,analyze(d));self.assertIn('Painting',text);self.assertNotIn('• Repair',text)
    def test_texas_address(self): self.assertIsNone(analyze(self.case(state='TX',forwarding=False))['deadline'])
    def test_florida_objection(self): self.assertEqual(analyze(self.case(state='FL'))['objection_deadline'],'2026-11-04')
    def test_ny_deadline(self): self.assertEqual(analyze(self.case(state='NY'))['deadline'],'2026-10-15')
    def test_unexplained(self): self.assertEqual(analyze(self.case(deductions=[]))['unaccounted'],1250)
    def test_overclaim_rejected(self):
        with self.assertRaises(ValueError): analyze(self.case(returned=2000))
    def test_nan_rejected(self):
        with self.assertRaises(ValueError): analyze(self.case(deposit='NaN'))
    def test_date_order(self):
        with self.assertRaises(ValueError): analyze(self.case(move_in='2026-10-02'))
    def test_zero_dispute(self):
        d=self.case(returned=2200,deductions=[])
        with self.assertRaises(ValueError): letter(d,analyze(d))
if __name__=='__main__': unittest.main()
