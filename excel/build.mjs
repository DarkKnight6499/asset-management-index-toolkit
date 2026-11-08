import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

// Configuration
const ROOT = process.cwd();
const INPUT = path.join(ROOT, 'examples/output/workbook_inputs.json');
const OUTPUT = path.join(ROOT, 'excel/asset_management_toolkit.xlsx');
const WORK = path.join(ROOT, '.work');
const REPORT = path.join(ROOT, 'examples/output/excel_verification.json');
const INSPECTION = OUTPUT + '.inspect.ndjson';
const STAGED_INSPECTION = path.join(WORK, 'workbook.inspect.ndjson');
const FONT = 'Arial';
const MONEY = '#,##0.00;(#,##0.00);0.00';
const DATE_FORMAT = 'yyyy-mm-dd';
const FIRST_TAX_ROW = 12;
const FIRST_BUY_ROW = 22;
const FIRST_BILL_ROW = 11;
const FIRST_AUM_ROW = 6;
const PURCHASE_LAST_ROW = 25;
const WASH_DAYS = 30;
const TIER1 = 1000000;
const TIER2 = 5000000;
const RATES = [.005, .0035, .0025];
const YEAR_DAYS = 365;
const TOLERANCE = 1e-7;

const input = JSON.parse(await fs.readFile(INPUT, 'utf8'));
const workbook = Workbook.create();
const names = ['Reconcile', 'Tax lots', 'Purchases', 'Billing', 'Daily AUM'];
const sheets = Object.fromEntries(names.map(name => [name, workbook.worksheets.add(name)]));
const serial = value => (Date.parse(value + 'T00:00:00Z') - Date.UTC(1899, 11, 30)) / 86400000;
const cell = (sheet, address, value) => { sheet.getRange(address).values = [[value]]; };
const formula = (sheet, address, value) => { sheet.getRange(address).formulas = [[value]]; };
const header = (sheet, address, values) => {
  sheet.getRange(address).values = [values];
  sheet.getRange(address).format.font.bold = true;
  sheet.getRange(address).format.wrapText = true;
  sheet.getRange(address).format.rowHeight = 32;
};
const base = (sheet, address, title) => {
  sheet.getRange(address).format.font.name = FONT;
  sheet.getRange(address).format.font.size = 10;
  sheet.getRange(address).format.rowHeight = 21;
  sheet.getRange(address).format.columnWidth = 16;
  sheet.getRange(address).setNumberFormat(MONEY);
  sheet.showGridLines = false;
  cell(sheet, 'A2', title);
  sheet.getRange('A2').format.font.bold = true;
  sheet.getRange('A2').format.font.size = 14;
};

const tax = sheets['Tax lots'];
const taxLast = FIRST_TAX_ROW + input.tax.attempts.length - 1;
const buys = input.tax.trades.filter(trade => trade.side === 'BUY');
const buyLast = FIRST_BUY_ROW + buys.length - 1;
base(tax, 'A1:N30', 'Tax-lot review (USD)');
cell(tax, 'A3', 'Sale date'); cell(tax, 'B3', serial(input.as_of));
tax.getRange('B3').setNumberFormat(DATE_FORMAT);
cell(tax, 'D3', 'Wash days'); cell(tax, 'E3', WASH_DAYS);
header(tax, 'A4:N4', ['Net gain/loss', '', '', 'Realized loss', '', '', 'Sale proceeds', '', '', 'Buy outflow', '', '', 'Ending cash', '']);
formula(tax, 'A5', `=SUM(M${FIRST_TAX_ROW}:M${taxLast})`);
formula(tax, 'D5', `=SUM(N${FIRST_TAX_ROW}:N${taxLast})`);
formula(tax, 'G5', `=SUM(K${FIRST_TAX_ROW}:K${taxLast})`);
formula(tax, 'J5', `=SUM(D${FIRST_BUY_ROW}:D${buyLast})`);
formula(tax, 'M5', '=B7+G5-J5');
cell(tax, 'A7', 'Opening cash'); cell(tax, 'B7', input.portfolio.cash);
cell(tax, 'A9', 'Synthetic proposals. Formulas apply the conservative sale guard; Python owns HIFO selection, replacement routing and buy locks.');
header(tax, 'A11:N11', ['Lot', 'Security', 'Group', 'Acquired', 'Available qty', 'Cost/share', 'Price/share', 'Requested qty', 'Window buys', 'Executed qty', 'Proceeds', 'Basis', 'Gain/loss', 'Loss amount']);
input.tax.attempts.forEach((attempt, index) => {
  const row = FIRST_TAX_ROW + index;
  tax.getRange(`A${row}:H${row}`).values = [[attempt.lot, attempt.security, attempt.group, serial(attempt.acquired), attempt.quantity, attempt.cost, attempt.price, attempt.requested_qty]];
  formula(tax, `I${row}`, `=SUMIFS(Purchases!$D$6:$D$${PURCHASE_LAST_ROW},Purchases!$B$6:$B$${PURCHASE_LAST_ROW},C${row},Purchases!$C$6:$C$${PURCHASE_LAST_ROW},">="&$B$3-$E$3,Purchases!$C$6:$C$${PURCHASE_LAST_ROW},"<="&$B$3+$E$3)`);
  formula(tax, `J${row}`, `=IF(OR(H${row}<0,H${row}>E${row},F${row}<0,G${row}<=0),NA(),IF(AND(G${row}<F${row},I${row}>0),0,H${row}))`);
  formula(tax, `K${row}`, `=J${row}*G${row}`);
  formula(tax, `L${row}`, `=J${row}*F${row}`);
  formula(tax, `M${row}`, `=K${row}-L${row}`);
  formula(tax, `N${row}`, `=MAX(0,-M${row})`);
});
tax.getRange(`D${FIRST_TAX_ROW}:D${taxLast}`).setNumberFormat(DATE_FORMAT);
tax.getRange('C11:C16').format.columnWidth = 24;
tax.getRange('E3').setNumberFormat('0');
header(tax, 'A21:D21', ['Planned buy', 'Quantity', 'Price/share', 'Outflow']);
buys.forEach((trade, index) => {
  const row = FIRST_BUY_ROW + index;
  tax.getRange(`A${row}:C${row}`).values = [[trade.security, trade.quantity, trade.price]];
  formula(tax, `D${row}`, `=B${row}*C${row}`);
});
cell(tax, 'A26', 'Changing sale inputs recalculates proceeds, basis and losses. Rerun Python to optimize quantities and update buy proposals.');
cell(tax, 'A28', 'Source: data/synthetic/portfolio.json and tax_lots.csv. Rule provenance: docs/source_verification.md, IRS Publication 550.');

const purchases = sheets.Purchases;
base(purchases, 'A1:F29', 'Known purchase ledger');
cell(purchases, 'A3', 'Synthetic household ledger. Include known future purchases. Any matching purchase blocks the whole proposed loss sale.');
header(purchases, 'A5:D5', ['Security', 'Declared group', 'Purchase date', 'Quantity']);
input.portfolio.purchases.forEach((purchase, index) => {
  purchases.getRange(`A${6+index}:D${6+index}`).values = [[purchase.security, input.portfolio.groups[purchase.security], serial(purchase.date), purchase.quantity]];
});
purchases.getRange(`C6:C${PURCHASE_LAST_ROW}`).setNumberFormat(DATE_FORMAT);
purchases.getRange('B5:B25').format.columnWidth = 28;
cell(purchases, 'A27', 'Editable ledger rows: 6 to 25. Declared groups require review; this workbook does not determine substantial identity.');
cell(purchases, 'A29', 'Source: IRS Publication 550 (2025), Chapter 4, Wash Sales. https://www.irs.gov/publications/p550');

const aum = sheets['Daily AUM'];
const aumLast = FIRST_AUM_ROW + input.daily_aum.length - 1;
base(aum, `A1:D${aumLast}`, 'Synthetic daily AUM (USD)');
cell(aum, 'A3', 'Seed 73421. Calendar-day observations; billing averages only active service days.');
header(aum, 'A5:C5', ['Client', 'Date', 'AUM']);
aum.getRange(`A${FIRST_AUM_ROW}:C${aumLast}`).values = input.daily_aum.map(row => [row.client, serial(row.date), Number(row.aum)]);
aum.getRange(`B${FIRST_AUM_ROW}:B${aumLast}`).setNumberFormat(DATE_FORMAT);
aum.getRange(`C${FIRST_AUM_ROW}:C${aumLast}`).format.columnWidth = 21;
aum.freezePanes.freezeRows(5);

const billing = sheets.Billing;
base(billing, 'A1:L20', 'SMA billing (USD)');
cell(billing, 'A4', 'Quarter start'); cell(billing, 'B4', serial(input.quarter_start));
cell(billing, 'D4', 'Quarter end'); cell(billing, 'E4', serial(input.quarter_end));
billing.getRange('B4').setNumberFormat(DATE_FORMAT); billing.getRange('E4').setNumberFormat(DATE_FORMAT);
cell(billing, 'A6', 'Tier 1 ceiling'); cell(billing, 'B6', TIER1);
cell(billing, 'D6', 'Tier 2 ceiling'); cell(billing, 'E6', TIER2);
cell(billing, 'G6', 'Year days'); cell(billing, 'H6', YEAR_DAYS);
cell(billing, 'A7', 'Tier 1 rate'); cell(billing, 'B7', RATES[0]);
cell(billing, 'D7', 'Tier 2 rate'); cell(billing, 'E7', RATES[1]);
cell(billing, 'G7', 'Tier 3 rate'); cell(billing, 'H7', RATES[2]);
for (const address of ['B7', 'E7', 'H7']) billing.getRange(address).setNumberFormat('0.00%');
billing.getRange('H6').setNumberFormat('0');
header(billing, 'A10:L10', ['Client', 'Opened', 'Closed (blank=active)', 'Active start', 'Active end', 'Active days', 'Average AUM', 'Tier 1 AUM', 'Tier 2 AUM', 'Tier 3 AUM', 'Annual fee', 'Quarter fee']);
const billLast = FIRST_BILL_ROW + input.billing.length - 1;
input.billing.forEach((invoice, index) => {
  const row = FIRST_BILL_ROW+index;
  billing.getRange(`A${row}:C${row}`).values = [[invoice.client, serial(invoice.opened), invoice.closed ? serial(invoice.closed) : null]];
  formula(billing, `D${row}`, `=MAX($B$4,B${row})`);
  formula(billing, `E${row}`, `=IF(C${row}="",$E$4,MIN($E$4,C${row}))`);
  formula(billing, `F${row}`, `=MAX(0,E${row}-D${row}+1)`);
  formula(billing, `G${row}`, `=IF(F${row}=0,0,AVERAGEIFS('Daily AUM'!$C$${FIRST_AUM_ROW}:$C$${aumLast},'Daily AUM'!$A$${FIRST_AUM_ROW}:$A$${aumLast},A${row},'Daily AUM'!$B$${FIRST_AUM_ROW}:$B$${aumLast},">="&D${row},'Daily AUM'!$B$${FIRST_AUM_ROW}:$B$${aumLast},"<="&E${row}))`);
  formula(billing, `H${row}`, `=IF(G${row}<0,NA(),MIN(G${row},$B$6))`);
  formula(billing, `I${row}`, `=MIN(MAX(G${row}-$B$6,0),$E$6-$B$6)`);
  formula(billing, `J${row}`, `=MAX(G${row}-$E$6,0)`);
  formula(billing, `K${row}`, `=H${row}*$B$7+I${row}*$E$7+J${row}*$H$7`);
  formula(billing, `L${row}`, `=ROUND(K${row}*F${row}/$H$6,2)`);
});
billing.getRange(`B${FIRST_BILL_ROW}:E${billLast}`).setNumberFormat(DATE_FORMAT);
billing.getRange(`F${FIRST_BILL_ROW}:F${billLast}`).setNumberFormat('0');
billing.getRange(`G10:L${billLast}`).format.columnWidth = 20;
cell(billing, 'K14', 'Total invoices'); formula(billing, 'L14', `=SUM(L${FIRST_BILL_ROW}:L${billLast})`);
cell(billing, 'A17', 'Hypothetical agreement: average active-day AUM, marginal tiers, actual calendar days/365, arrears, rounded per invoice.');
cell(billing, 'A19', 'SMA-003 is held for onboarding and excluded from invoices. Source: synthetic daily_aum.csv and clients.json.');

const reconcile = sheets.Reconcile;
base(reconcile, 'A1:D18', 'Python and Excel reconciliation');
cell(reconcile, 'A3', 'All data is synthetic. Differences compare live Excel formulas with the saved Python run.');
header(reconcile, 'A5:D5', ['Metric', 'Live Excel', 'Python output', 'Difference']);
reconcile.getRange('A5:A18').format.columnWidth = 34;
const expectations = [
  ['Net realized gain/loss', "='Tax lots'!A5", input.tax.realized_gain],
  ['Realized loss', "='Tax lots'!D5", input.tax.realized_loss],
  ['Sale proceeds', "='Tax lots'!G5", input.tax.trades.filter(row=>row.side==='SELL').reduce((total,row)=>total+row.cash_flow,0)],
  ['Ending cash', "='Tax lots'!M5", input.tax.cash],
  ['Invoices', '=Billing!L14', input.billing.reduce((total,row)=>total+row.fee,0)],
];
expectations.forEach(([label, expression, expected], index) => {
  const row=6+index;
  cell(reconcile, `A${row}`, label); formula(reconcile, `B${row}`, expression);
  cell(reconcile, `C${row}`, expected); formula(reconcile, `D${row}`, `=B${row}-C${row}`);
});
cell(reconcile, 'A13', 'Baseline formulas reconcile to Python.');
cell(reconcile, 'A15', 'Edit input cells to explore a scenario. Reconciliation differences then measure departure from the saved run.');
cell(reconcile, 'A17', 'Methods and limits: docs/methodology.md and docs/limitations.md. No live filing data or tax saving is assumed.');

workbook.recalculate();
const differences = reconcile.getRange('D6:D10').values.flat();
if (differences.some(value => typeof value !== 'number' || Math.abs(value)>TOLERANCE)) throw new Error('Reconciliation failed: '+JSON.stringify(differences));
// Input changes verify recalculation independently of saved formula values.
const originalPrice = tax.getRange('G12').values[0][0];
cell(tax, 'G12', originalPrice-1);
const priceLoss = tax.getRange('D5').values[0][0];
if (Math.abs(priceLoss-(input.tax.realized_loss+100))>TOLERANCE) throw new Error('Price sensitivity failed');
cell(tax, 'G12', originalPrice);
const savedDays = tax.getRange('E3').values[0][0];
cell(tax, 'E3', 19);
const day19Quantity = tax.getRange('J14').values[0][0];
if (!(day19Quantity > 0)) throw new Error('Wash-window sensitivity failed');
cell(tax, 'E3', savedDays);
const originalRate = billing.getRange('B7').values[0][0];
cell(billing, 'B7', originalRate+.001);
const increasedInvoice = billing.getRange('L11').values[0][0];
if (Math.abs(increasedInvoice-(input.billing[0].fee+252.05))>.011) throw new Error('Billing sensitivity failed');
cell(billing, 'B7', originalRate);
workbook.recalculate();
const errors = await workbook.inspect({kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options:{useRegex:true,maxResults:50}, maxChars:2000});
console.log(errors.ndjson);
console.log((await workbook.inspect({kind:'table',range:'Reconcile!A5:D10',include:'values,formulas',tableMaxRows:6,tableMaxCols:4,maxChars:2500})).ndjson);
await fs.mkdir(WORK, {recursive:true});
for (const [name, range] of [['Reconcile','A2:D17'],['Tax lots','A2:N28'],['Purchases','A2:F29'],['Billing','A2:L19'],['Daily AUM','A2:D17']]) {
  const preview = await workbook.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(WORK,name.replaceAll(' ','_')+'.png'), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(OUTPUT);
try { await fs.rename(INSPECTION, STAGED_INSPECTION); } catch (error) { if (error.code !== 'ENOENT') throw error; }
await fs.writeFile(REPORT,JSON.stringify({author:input.author,engine:'@oai/artifact-tool',baseline_differences:differences,
  tested:['price sensitivity','wash window sensitivity','billing rate sensitivity','formula error scan','all five sheets rendered'],
  native_excel_checked:false},null,2)+'\n');
console.log('Exported '+OUTPUT);
