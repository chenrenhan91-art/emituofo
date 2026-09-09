const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(require('node:path').join(__dirname, '../index.html'), 'utf8');
function source(name, next) { return html.slice(html.indexOf(`    function ${name}(`), html.indexOf(`    function ${next}(`)); }
const context = { S: {isReadingAll:false,readingIndex:-1,sutra:0}, speakGen:0,
 SUTRA_DATABASE:[{id:'a',verses:[{text:'a1'},{text:'a2'}]},{id:'b',verses:[{text:'b1'},{text:'b2'}]}],
 calls:[],timers:[],button:{},$:()=>context.button,
 markLastRead(){},highlight(){},prefetchVerse(){},recordRecitation(){throw Error('unexpected completion');},
 stopSpeech(){context.speakGen++;context.S.isReadingAll=false;context.S.readingIndex=-1;},
 speak(text,done,meta){context.calls.push({text,done,meta});},
 setTimeout(fn){context.timers.push(fn);}
};
vm.createContext(context);vm.runInContext(source('playAll','hitMuyu'),context);
context.playAll();context.calls[0].done(); // Old audio ends and schedules its next paragraph.
context.stopSpeech();context.S.sutra=1;context.playAll();
context.timers[0]();
assert.deepEqual(context.calls.map(x=>x.text),['a1','b1'],'stale timer must not play an old sutra');
context.calls[1].done();context.timers[1]();
assert.deepEqual(context.calls.map(x=>x.text),['a1','b1','b2']);
let completed=false, fallback=false, stopped=false;
const failContext={speakGen:1,reciter:{pause(){},play(){return Promise.resolve();}},
 recitationRate:()=>1,verseAudioUrl:()=>'/recording.mp3',
 speakTTS(){fallback=true;},stopSpeech(){stopped=true;failContext.speakGen++;},toast(){}};
vm.createContext(failContext);vm.runInContext(source('speak','playOne'),failContext);
failContext.speak('text',()=>{completed=true;},{id:'a',i:0});failContext.reciter.onerror();
assert(stopped);assert(!completed);assert(!fallback);
console.log('PASS: stale callbacks are ignored; missing audio stops without false completion or voice fallback.');

const loopContext = { S: {isReadingAll:false,isLooping:false,readingIndex:-1,sutra:0}, speakGen:0,
 SUTRA_DATABASE:[{id:'a',verses:[{text:'a1'},{text:'a2'}]}], calls:[], timers:[], button:{},
 $:()=>loopContext.button, markLastRead(){},highlight(){},prefetchVerse(){},
 stopSpeech(){loopContext.speakGen++;loopContext.S.isReadingAll=false;loopContext.S.isLooping=false;},
 speak(text,done,meta){loopContext.calls.push({text,done,meta});}, setTimeout(fn){loopContext.timers.push(fn);}
};
vm.createContext(loopContext);vm.runInContext(source('loopAll','hitMuyu'),loopContext);
loopContext.loopAll();
assert.equal(loopContext.calls[0].text,'a1');
loopContext.calls[0].done();loopContext.timers[0]();
assert.equal(loopContext.calls[1].text,'a2');
loopContext.calls[1].done();loopContext.timers[1]();
loopContext.timers[2]();
assert.equal(loopContext.calls[2].text,'a1','the selected sutra restarts after its final verse');
loopContext.loopAll();
assert.equal(loopContext.S.isLooping,false,'second click pauses the loop');
console.log('PASS: loop playback restarts after the final verse and pauses on second click.');
