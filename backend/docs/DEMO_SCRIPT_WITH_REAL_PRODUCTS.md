# Updated Demo Script with Real iHerb Products

This demo script uses your actual iHerb product catalog for more realistic fake memories and demonstrations.

## Step 1: Inject Fake Memories with Real Products

### 1.1 Create a Demo User with Comprehensive Memories

VXNlcjo0OA==

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_client_123/inject" \
  -H "Content-Type: application/json" \
  -d '{
    "num_memories": 25,
    "memory_types": ["user_preference", "product_interaction", "conversation_theme", "order_history"]
  }'
```

### 1.2 Add Specific Order History with Real Products

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_client_123/inject-orders" \
  -H "Content-Type: application/json" \
  -d '{"num_orders": 8}'
```

### 1.3 Add Product Reviews for Real Products

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_client_123/inject-reviews" \
  -H "Content-Type: application/json" \
  -d '{"num_reviews": 6}'
```

### 1.4 Verify Memories Were Created

```bash
curl "http://localhost:4003/v1/memory/debug/store/demo_client_123"
```

## Step 2: Frontend Demo Questions with Real Product Context

### 2.1 Gut Health & Probiotics Focus

**Question**: _"I have digestive issues and need help with gut health"_

**Expected Demo Points**:

- System should reference probiotics like "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules"
- Should mention "California Gold Nutrition, Probiotics with Lactobacillus acidophilus"
- May reference past experiences with "Jarrow Formulas, Jarro-Dophilus EPS"

### 2.2 Sleep Support & Stress Management

**Question**: _"I'm having trouble sleeping and feel stressed"_

**Expected Demo Points**:

- System should recommend "ALLMAX, Melatonin, 60 Capsules"
- Should suggest "Swanson, Sleep Essentials, 60 Vegan Capsules"
- May reference "Super Nutrition, Stress Support with L-Theanine, Ashwagandha"

### 2.3 Athletic Performance & Recovery

**Question**: _"I'm training for a marathon and need energy and recovery support"_

**Expected Demo Points**:

- System should recommend "Doctor's Best, L-Citrulline Powder" for performance
- Should suggest "California Gold Nutrition, Sport, Creatine Monohydrate"
- May reference "Doctor's Best, Pure L-Arginine Powder" for circulation

### 2.4 Anti-Aging & Collagen Support

**Question**: _"I want to support healthy aging and skin health"_

**Expected Demo Points**:

- System should recommend "Vital Proteins, Collagen Peptides, Unflavored, 20 oz"
- Should suggest "California Gold Nutrition, CollagenUP®, Hydrolyzed Marine Collagen Peptides"
- May reference "Sports Research, Marine Collagen" for joint support

### 2.5 Heart Health & Energy

**Question**: _"I'm concerned about heart health and need more energy"_

**Expected Demo Points**:

- System should recommend "NOW Foods, CoQ10, 400 mg, 60 Softgels"
- Should suggest "NOW Foods, Ubiquinol CoQH-CF, 50 mg, 60 Softgels"
- May reference "Life Extension, Vitamin B12, Methylcobalamin" for energy

### 2.6 Stress & Adaptogens

**Question**: _"I need help managing stress and anxiety"_

**Expected Demo Points**:

- System should recommend "NutraBio, KSM-66®, Ashwagandha, 60 Capsules"
- Should suggest "Primaforce, KSM-66, Ashwagandha Root Extract"
- May reference past positive experiences with adaptogens

## Step 3: Advanced Demo Scenarios with Real Products

### 3.1 Product-Specific Memory Retrieval

Ask: _"What do you know about my previous experiences with probiotics?"_

Expected: System should reference specific probiotic products from fake memories like:

- "You previously purchased NOW Foods, Probiotic-10 and were satisfied"
- "You had positive results with California Gold Nutrition probiotics"

### 3.2 Category-Based Recommendations

Ask: _"I'm looking for sleep support products"_

Expected: System should recommend from your actual catalog:

- "ALLMAX, Melatonin, 60 Capsules"
- "Swanson, Sleep Essentials, 60 Vegan Capsules"
- "NATURELO, Sleep Formula, 60 Vegetarian Capsules"

### 3.3 Brand Preference Recognition

Ask: _"I prefer NOW Foods products"_

Expected: System should prioritize NOW Foods products from your catalog:

- "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules"
- "NOW Foods, CoQ10, 400 mg, 60 Softgels"
- "NOW Foods, Ubiquinol CoQH-CF, 50 mg, 60 Softgels"

## Step 4: Demo Script for Client Presentation

### Opening (30 seconds)

_"Today I'll show you how our AI assistant learns from every interaction to provide increasingly personalized recommendations using our actual iHerb product catalog. Let me set up a demo user with realistic purchase history."_

### Memory Injection (1 minute)

_"First, I'm injecting realistic user data including past orders with real products like NOW Foods probiotics, California Gold Nutrition supplements, and Swanson sleep aids. This simulates a returning customer with established preferences."_

### Gut Health Personalization (2 minutes)

_"When I ask about digestive health, notice how the system immediately considers my health condition and suggests appropriate probiotics from our catalog, referencing my past experiences with specific brands."_

### Sleep & Stress Management (2 minutes)

_"The system also remembers my sleep struggles and can suggest related products like melatonin and stress support formulas. It knows I prefer certain brands and avoids products I've had issues with."_

### Athletic Performance (1 minute)

_"For athletic performance, the system references my training goals and suggests products like L-Citrulline for circulation and creatine for muscle support, all from our actual product catalog."_

### Memory Consolidation (1 minute)

_"Over time, the system consolidates all these interactions to build a comprehensive profile. Let me show you what insights it has developed about this user's preferences and past experiences."_

### Closing (30 seconds)

_"This creates a shopping experience that gets better with every interaction, just like talking to a knowledgeable personal shopper who remembers everything about your preferences and our actual product catalog."_

## Step 5: Real Product Examples in Fake Memories

The system will now create fake memories like:

### User Preference Memory

```json
{
	"content": "User prefers NOW Foods brand supplements and is interested in gut health management. Enjoys running and needs products that support digestive health and athletic performance.",
	"memory_type": "user_preference",
	"metadata": {
		"health_condition": "digestive_issues",
		"preferred_brand": "NOW Foods",
		"activity": "running"
	}
}
```

### Product Interaction Memory

```json
{
	"content": "User purchased NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules and was satisfied with the results after 2 weeks",
	"memory_type": "product_interaction",
	"metadata": {
		"product_name": "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules",
		"interaction_type": "purchase",
		"satisfaction": "positive"
	}
}
```

### Order History Memory

```json
{
	"content": "User placed an order on 2024-01-15 containing: ALLMAX, Melatonin, 60 Capsules, Swanson, Sleep Essentials, 60 Vegan Capsules. Order was delivered successfully and user was satisfied with sleep improvement.",
	"memory_type": "order_history",
	"metadata": {
		"order_date": "2024-01-15",
		"products": ["ALLMAX, Melatonin, 60 Capsules", "Swanson, Sleep Essentials, 60 Vegan Capsules"],
		"order_status": "delivered",
		"satisfaction": "satisfied"
	}
}
```

## Step 6: Demo Success Indicators

The demo is successful if the system:

- ✅ References specific iHerb products from your catalog
- ✅ Mentions past orders with real product names
- ✅ Respects brand preferences (NOW Foods, California Gold Nutrition, etc.)
- ✅ Considers health conditions with appropriate product categories
- ✅ Builds on previous conversation context with real products
- ✅ Provides increasingly personalized recommendations from your actual catalog

This updated demo script will showcase the full power of your memory and personalization system using your real iHerb product catalog!
