/**
 * Data Types
 * 
 * 여섯개의 Primitive Type과
 * 한 개의 오브젝트 타입이 있다.
 * 
 * 1) Number (숫자)
 * 2) String (문자열)
 * 3) Boolean (불리언)
 * 4) undefined (언디파인드)
 * 5) null (널)
 * 6) Symbol (심볼)
 * 
 * 7) Object (객체)
 *    Function
 *    Array
 *    Object
 */
const age = 35;
const temperature = -10;
const pi = 3.14;

console.log(typeof age);
console.log(typeof temperature);
console.log(typeof pi);
console.log('-----------------');

const infinity = Infinity;
const nInfinity = -Infinity;

console.log(typeof infinity);
console.log(typeof nInfinity);
console.log('-----------------');

const ive = "'아이브' 안유진" // 작은따옴표를 넣고 싶으면 큰따옴표로 감싸주어야 함.
const codeFactory = '"코"드팩토리' // 반대도 마찬가지.

console.log(typeof ive);
console.log(typeof codeFactory);
console.log(ive);
console.log(codeFactory);


const myCar = {  // [1] 변수 선언 및 객체 리터럴 시작
    brand: "Hyundai", // [2] 프로퍼티 (Property)
    model: "Ionic 5",
    speed: 0,
    accelerate: function () { this.speed += 10; } // [3] 메서드 (Method)
};

console.log(myCar);
