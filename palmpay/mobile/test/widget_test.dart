import 'package:flutter/material.dart';

import 'package:flutter_test/flutter_test.dart';



import 'package:palmpay/core/constants/veinpay_brand.dart';

import 'package:palmpay/shared/widgets/veinpay_logo.dart';



void main() {

  testWidgets('VeinPay branding smoke test', (WidgetTester tester) async {

    await tester.pumpWidget(

      const MaterialApp(

        home: Scaffold(

          body: Center(

            child: VeinPayLogo(size: VeinPayBrand.logoMd),

          ),

        ),

      ),

    );

    expect(find.byType(VeinPayLogo), findsOneWidget);

  });

}


