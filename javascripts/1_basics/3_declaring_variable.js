/**
 * Variable 선언하기
 * 
 * 1) var - 더이상 쓰지 않는다.
 * 2) let
 * 3) const
 */
var name = '코드팩토리';
console.log(name);

var age = 32;
console.log(age);

let ive = '아이브';
console.log(ive);

/**
 * let과 var로 선언하면
 * 값을 추후 변경할 수 있다.
 */
ive = '안유진';
console.log(ive);

const newJeans = '뉴진스';
console.log(newJeans);

/**
 * const로 선언하면
 * 값을 추후 변경할 수 없다.
 */

// newJeans = '코드팩토리';

/**
 * 선언과 할당
 * 
 * 1) 변수를 선언하는 것.
 * 2) 할당
 */
var name = '코드팩토리';
console.log(name);

let girlFriend;
console.log(girlFriend); // 선언만 했고 할당을 하지 않았으므로 undefined 출력.

const girlFriend2; // 값이 바뀔 수 없기 때문에 반드시 할당이 되어야함.